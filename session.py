"""A debug session, equivalent to a debugger instance like a `pdb` process or a PyCharm debugger tab."""
from pathlib import Path
from signal import SIGTERM
from typing import Any, Callable, Iterator

from dap import DAPClient, Event, InitializedEvent
from dap.protocol import ErrorResponse
import psutil

from breakpoints import Breakpoints, File
from constants import TEMP_DIR
from enums import DebuggerState, SuspendPolicy
from exceptions import DAPError, FrameNotFound, SessionStateError, ThreadNotFound
from models import Breakpoint, SessionStatus, StackFrame, Thread, Variable
from threads import Threads
from utils import connect_to_port, fetch_line_text


class Session:
    """A debug session, equivalent to a debugger instance like a `pdb` process or a PyCharm debugger tab."""
    CHUNK_SIZE = 65536

    # TODO: handle closing the socket when we need to, not sure when that is, figure it out

    # def __exit__(self, exc_type, exc_val, traceback) -> None:
    #     self.sock.__exit__(exc_type, exc_val, traceback)

    def __init__(
        self, session_id: str, project_path: str, port: int, timeout: int, we_own: bool, pid: int | None = None,
    ):
        """Timeout is in milliseconds."""
        self.breakpoints = Breakpoints()
        self.breakpoints_muted: bool = False
        self.client = DAPClient(clientID=session_id, clientName="JuneBug", locale="en-US")
        self.current_position: Breakpoint | None = None
        self.debugee_pid = pid
        self.has_configuration_done = False
        self.project_path = project_path
        self.session_id = session_id
        self.sock = connect_to_port(port, timeout / 1000.0)
        self.state: DebuggerState = DebuggerState.PAUSED
        self.std_out_path = str(TEMP_DIR / f"{session_id}.stdout.txt") if we_own else None
        self.std_err_path = str(TEMP_DIR / f"{session_id}.stderr.txt") if we_own else None
        self.threads = Threads()
        self.we_own = we_own

        # set up the event iterator
        self._event_iterator = self._pull()

        # empty push on a just-created client sends the initialize request
        self._send()
        # pull until we get the InitializedEvent, this blocks until it is received.
        self._pull_until(lambda e: isinstance(e, InitializedEvent))
        # nothing can happen until we attach, let's do that automatically
        self._attach()
        # always get the initial registry of threads at this point, because we can.
        self.list_threads()
        # the first thread always starts paused
        self.threads.pause_at_start()

    def _pull(self) -> Iterator[Event]:
        """
        An unbounded iterator that returns every event sent by the DAP server.
        This should only ever be called once, in the constructor of the session.
        After that, you should use `self._event_iterator`.
        """
        while True:
            yield from self.client.recv(self.sock.recv(self.CHUNK_SIZE))

    def _pull_until(self, matcher: Callable[[Event], bool]) -> Event:
        """Pull events from the DAP client until the given matcher function returns true on an event, then return that event."""
        for event in self._event_iterator:
            print(event.model_dump_json(indent=2))  # for easy logging
            if isinstance(event, ErrorResponse):
                # yes, the typing says this is impossible, but trust me, it happens
                raise DAPError(event)
            self._handle_event(event)
            if matcher(event):
                return event

    def _handle_event(self, event: Event) -> None:
        """
        Handle any state updates that need to happen when we see certain events.
        This gets passed every event that we pull.
        """
        if event.body is not None and "threadId" in event.body:
            self.threads.update(event)

        if event.event == "stopped":
            self.threads.set_current(event.body["threadId"])
            if hit_breakpoint_ids := event.body.get("hitBreakpointIds"):
                self.current_position = self.breakpoints.get_breakpoint_by_id(hit_breakpoint_ids[0])
            self.state = DebuggerState.PAUSED

        if event.event == "terminated":
            # Just in case the agent tries to re-use or inspect a closed session, clear all this out
            self.current_position = None
            self.threads.clear()
            self.breakpoints.clear()
            self.breakpoints_muted = False
            self.state = DebuggerState.STOPPED

        # TODO: handle other passive events that update our internal model of the debugger's state here

    def _send(self):
        self.sock.sendall(self.client.send())

    def assert_state(self, expected_state: DebuggerState) -> None:
        """Assert that this session is in the given state. Raises a `SessionStateError` if not."""
        if self.state != expected_state:
            raise SessionStateError(expected_state, self.state)

    def get_current_thread_id(self) -> int | None:
        self.list_threads()
        return self.threads.get_current_thread_id()

    def get_status(self) -> SessionStatus:
        """Get the status of this session."""
        if self.state != DebuggerState.STOPPED:  # don't try talking anymore if we're stopped
            self.list_threads()  # do a list_threads to pull the most recent messages from the DAP server
        return SessionStatus(
            id=self.session_id,
            state=self.state,
            debugee_pid=self.debugee_pid,
            std_out_path=self.std_out_path,
            std_err_path=self.std_err_path,
            breakpoints_muted=self.breakpoints_muted,
            current_position=self.current_position,
        )

    def list_breakpoints(self, path: Path | None) -> list[Breakpoint]:
        """
        List all breakpoints, sorted by file, and then by line number.
        Lists them only for the given file if one is specified, otherwise lists all of them.
        """
        if path is None:
            return self.breakpoints.list_breakpoints()
        else:
            return self.breakpoints.list_breakpoints_for_file(path)

    def list_variables(self, frame_id: int, show_hidden: bool, depth: int) -> list[Variable]:
        """List all variables of a given frame ID, down to a given depth, showing hidden ones if requested."""

        self.assert_state(DebuggerState.PAUSED)
        scope_ids: list[int] = [
            dap_scope["variablesReference"] for dap_scope in self._scopes(frame_id).body["body"]["scopes"]
        ]

        variables: list[Variable] = []
        for scope_id in scope_ids:
            self._fetch_variable_children(scope_id, variables, show_hidden, depth + 1)

        return variables

    def list_stack_frames(self, thread_id: int | None) -> list[StackFrame]:
        """List all stack frames of a given thread ID. Errors appropriately if no thread ID is given."""
        if thread_id is None:
            raise Exception("No thread ID specified, and there is no current thread listed.")
        frames = self._stack_trace(thread_id).body["body"]["stackFrames"]
        return [StackFrame.from_dap(frame) for frame in frames]

    def list_threads(self) -> list[Thread]:
        """Get all threads, sorted by id."""
        return self.threads.refresh(self._fetch_threads())

    def pause(self):
        """Pause this session."""
        self._pause(self.list_threads()[0].id)
        # TODO: set current position somehow?
        self.state = DebuggerState.PAUSED

    def resume(self):
        """Resume this session. Does not block."""
        # we're going to need to list threads anyway in most cases
        # and listing threads pulls the latest events to update our state and current_position, which we then check
        threads = self.list_threads()
        if self.state == DebuggerState.RUNNING:
            return  # Don't double run
        if not self.has_configuration_done:
            # this has to happen once per session, and only once, and it automatically resumes all threads
            self._configuration_done()
            self.has_configuration_done = True
        else:
            self._continue_execution(threads[0].id)
        self.current_position = None
        self.state = DebuggerState.RUNNING

    def set_breakpoint(
        self, path: Path, line: int, condition: str | None, temporary: bool, suspend_policy: SuspendPolicy,
    ) -> Breakpoint:
        """Set a new breakpoint. See the docstring on the `Breakpoints` class to understand why this is so complex."""
        line_text = fetch_line_text(path, line)[:120]
        bp = self.breakpoints.add_breakpoint(path, line, line_text, condition, temporary, suspend_policy)
        self.breakpoints.refresh(self._set_breakpoints(self.breakpoints.get_file(path)))
        return bp

    def stop(self) -> None:
        """Stop this session."""
        self._disconnect()
        if self.we_own:
            psutil.Process(self.debugee_pid).send_signal(SIGTERM)

    def remove_breakpoint(self, path: Path, line: int) -> None:
        """Remove a breakpoint. Idempotent, no-op on nonexistent breakpoint."""
        did_remove = self.breakpoints.remove_breakpoint(path, line)
        if did_remove:
            self.breakpoints.refresh(self._set_breakpoints(self.breakpoints.get_file(path)))

    def set_breakpoints_muted(self, breakpoints_muted: bool):
        """Set all breakpoints to muted."""
        self.breakpoints_muted = breakpoints_muted
        # for every file we have
        for file in self.breakpoints.list_files():
            if breakpoints_muted:
                # clear each file by sending a blank version of it
                # DO NOT refresh our breakpoints internally
                self._set_breakpoints(File(file.path))
            else:
                # re-send the real file to DAP if we're unmuting
                # do refresh our breakpoints internally, this changes their IDs
                self.breakpoints.refresh(self._set_breakpoints(file))

    def wait_for_pause(self):
        """Wait for the debugger to pause on a line on its own. Only blocks, does not send anything to DAP."""
        if self.state == DebuggerState.PAUSED:
            return  # we are already paused, don't just block forever
        self._pull_until(lambda e: e.event == "stopped" or e.event == "terminated")

    def _fetch_variable_children(
        self, variable_id: int, output: list[Variable] | None, show_hidden: bool, depth: int,
    ) -> None:
        """Fetch the children of a variable, into the given output array, recursively, down to the given depth."""
        if depth == 0 or variable_id == 0 or output is None:
            return

        for dap_variable in self._variables(variable_id).body["body"]["variables"]:
            child = Variable.from_dap(dap_variable)
            # All the variables we want to hide by default, in python, luckily, do not have a type
            if child.type or show_hidden:
                output.append(child)
                self._fetch_variable_children(child.id, child.children, show_hidden, depth - 1)

    # DAP commands

    def _attach(self) -> Event:
        """Attach to a running program."""
        # this is a secret option that allows us to see stack frames from libraries
        self.client.attach(justMyCode=False)
        self._send()
        return self._pull_until(lambda e: e.event == "initialized")

    def _cancel(self, request_id: int | None = None, progress_id: str | None = None) -> Event:
        """Cancel a request or progress."""
        self.client.cancel(request_id, progress_id)
        self._send()
        return self._pull_until(lambda e: True)

    def _configuration_done(self) -> Event:
        """Indicate that configuration is done."""
        self.client.configuration_done()
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "configurationDone")
        # There are extra events returned after this, that we don't handle, the next command will see it

    def _continue_execution(self, thread_id: int) -> None:
        """Continue execution. Does not block."""
        self.client.continue_execution(thread_id)
        self._send()

    def _disconnect(self) -> Event:
        """Disconnect from the debug adapter."""
        self.client.disconnect()
        self._send()
        return self._pull_until(lambda e: e.event == "terminated")

    def _evaluate(self, expression: str, frame_id: int | None = None, **kwargs) -> Event:
        """Evaluate an expression."""
        self.client.evaluate(expression, frame_id, **kwargs)
        self._send()
        return self._pull_until(lambda e: True)

    def _launch(self, program: str, **kwargs) -> Event:
        """Launch a program in the debugger."""
        self.client.launch(program, **kwargs)
        self._send()
        return self._pull_until(lambda e: True)

    def _next(self, thread_id: int) -> Event:
        """Step to the next line."""
        self.client.next(thread_id)
        self._send()
        return self._pull_until(lambda e: True)

    def _pause(self, thread_id: int) -> Event:
        """Pause execution."""
        self.client.pause(thread_id)
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "pause")

    def _scopes(self, frame_id: int) -> Event:
        """Get the scopes for a stack frame."""
        self.client.scopes(frame_id)
        self._send()
        try:
            return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "scopes")
        except DAPError as dap_error:
            e = dap_error.event
            if e.command == "scopes" and e.message.startswith("Wrong ID sent from the client"):
                raise FrameNotFound(frame_id)
            raise

    def _set_breakpoints(self, file: File) -> Event:
        """Set breakpoints for a file."""
        self.client.set_breakpoints({"path": str(file.path)}, [bp.to_dap() for bp in file.list_breakpoints()])
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "setBreakpoints")

    def _set_exception_breakpoints(self, filters: list[str]) -> Event:
        """Set exception breakpoints."""
        self.client.set_exception_breakpoints(filters)
        self._send()
        return self._pull_until(lambda e: True)

    def _set_function_breakpoints(self, breakpoints: list[dict[str, Any]]) -> Event:
        """Set function breakpoints."""
        self.client.set_function_breakpoints(breakpoints)
        self._send()
        return self._pull_until(lambda e: True)

    def _set_variable(self, variables_reference: int, name: str, value: str) -> Event:
        """Set the value of a variable."""
        self.client.set_variable(variables_reference, name, value)
        self._send()
        return self._pull_until(lambda e: True)

    def _source(self, source_reference: int) -> Event:
        """Get the source code."""
        self.client.source(source_reference)
        self._send()
        return self._pull_until(lambda e: True)

    def _stack_trace(self, thread_id: int) -> Event:
        """Get the stack trace."""
        self.client.stack_trace(thread_id)
        self._send()
        try:
            return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "stackTrace")
        except DAPError as dap_error:
            e = dap_error.event
            if e.command == "stackTrace" and e.message.startswith("Wrong ID sent from the client"):
                raise ThreadNotFound(thread_id)
            raise

    def _step_in(self, thread_id: int) -> Event:
        """Step into the current line."""
        self.client.step_in(thread_id)
        self._send()
        return self._pull_until(lambda e: True)

    def _step_out(self, thread_id: int) -> Event:
        """Step out of the current function."""
        self.client.step_out(thread_id)
        self._send()
        return self._pull_until(lambda e: True)

    def _fetch_threads(self) -> Event:
        """Get all threads."""
        self.client.threads()
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "threads")

    def _variables(self, variables_reference: int) -> Event:
        """Get variables in a scope."""
        self.client.variables(variables_reference)
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "variables")
