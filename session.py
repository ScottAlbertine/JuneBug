"""A debug session, equivalent to a debugger instance like a `pdb` process or a PyCharm debugger tab."""
from pathlib import Path
from signal import SIGTERM

import psutil

from breakpoints import Breakpoints, File
from constants import Message, TEMP_DIR
from dap import DAPClient
from enums import SessionState, StepDirection
from exceptions import SessionStateError
from models import Breakpoint, SessionStatus, StackFrame, StackFrames, Thread, Variable
from threads import Threads
from utils import fetch_line_text


class Session:
    """A debug session, equivalent to a debugger instance like a `pdb` process or a PyCharm debugger tab."""

    def __init__(
        self,
        session_id: str,
        project_path: str,
        host: str,
        port: int,
        timeout: int,
        we_own: bool,
        pid: int | None = None,
    ):
        """Timeout is in milliseconds."""
        self.breakpoints = Breakpoints()
        self.breakpoints_muted: bool = False
        self.current_position: Breakpoint | None = None
        self.debugee_pid = pid
        self.has_configuration_done = False
        self.project_path = project_path
        self.session_id = session_id
        self.state: SessionState = SessionState.UNKNOWN
        self.std_out_path = str(TEMP_DIR / f"{session_id}.stdout.txt") if we_own else None
        self.std_err_path = str(TEMP_DIR / f"{session_id}.stderr.txt") if we_own else None
        self.threads = Threads()
        self.we_own = we_own

        self._client = DAPClient(session_id, host, port, timeout, self._handle_message)

        # always get the initial registry of threads at this point, because we can.
        self.list_threads()
        # if we own it, we always launch with `--wait-for-client`, so all threads are paused on start
        if self.we_own:
            self.state: SessionState = SessionState.PAUSED
            self.threads.pause_at_start()
        else:
            # TODO: figure out how to get the state here, when we attach to an existing process that may or may not have `--wait-for-client` set on its launch
            # TODO: probably do that instead of hard setting paused above
            # self.state = something
            pass

        # Technically, we could get the current position here, however, in many cases that takes 600ms, or is misleading, or both.
        # self.current_position = self.fetch_current_position(self.threads.get_current_thread_id())

    # session commands

    def get_current_thread_id(self) -> int | None:
        self.list_threads()
        return self.threads.get_current_thread_id()

    def get_stack_trace(
        self, thread_id: int | None, limit: int | None = None, offset: int | None = None,
    ) -> StackFrames:
        """
        List all stack frames of a given thread ID. Errors appropriately if no thread ID is given.
        IMPORTANT: On a paused thread, this takes 20ms. On a running thread, it takes 600ms.
        """
        if thread_id is None:
            raise Exception("No thread ID specified, and there is no current thread listed.")
        dap_stack_trace = self._client.stack_trace(thread_id, limit, offset)["body"]
        frames = [StackFrame.from_dap(frame) for frame in dap_stack_trace["stackFrames"]]
        return StackFrames(frames=frames, thread_id=thread_id, total_frames=dap_stack_trace["totalFrames"])

    def get_status(self) -> SessionStatus:
        """Get the status of this session."""
        if self.state != SessionState.STOPPED:  # don't try talking anymore if we're stopped
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

        self.assert_state(SessionState.PAUSED)
        scope_ids: list[int] = [
            dap_scope["variablesReference"] for dap_scope in self._client.scopes(frame_id)["body"]["scopes"]
        ]

        variables: list[Variable] = []
        for scope_id in scope_ids:
            self._fetch_variable_children(scope_id, variables, show_hidden, depth + 1)

        return variables

    def list_threads(self) -> list[Thread]:
        """Get all threads, sorted by id."""
        return self.threads.refresh(self._client.threads())

    def pause(self):
        """Pause this session."""
        self._client.pause(self.list_threads()[0].id)
        self.current_position = self.fetch_current_position(self.get_current_thread_id())
        self.state = SessionState.PAUSED

    def remove_breakpoint(self, path: Path, line: int) -> None:
        """Remove a breakpoint. Idempotent, no-op on nonexistent breakpoint."""
        did_remove = self.breakpoints.remove_breakpoint(path, line)
        if did_remove:
            self.breakpoints.refresh(self.set_breakpoints(self.breakpoints.get_file(path)))

    def resume(self):
        """Resume this session. Does not block."""
        # we're going to need to list threads anyway in most cases
        # and listing threads pulls the latest messages to update our state and current_position, which we then check
        threads = self.list_threads()
        if self.state == SessionState.RUNNING:
            return  # Don't double run
        if not self.has_configuration_done:
            # this has to happen once per session, and only once, and it automatically resumes all threads
            self._client.configuration_done()
            self.has_configuration_done = True
        else:
            self._client.continue_execution(threads[0].id)
        self.current_position = None
        self.state = SessionState.RUNNING

    def run_to_line(self, path: Path, line: int) -> None:
        """
        Set a temporary breakpoint at the given location, resume execution until it is hit, ignoring all breakpoints until that happens.
        Blocks until the specifically set breakpoint is hit.
        """
        was_muted = self.breakpoints_muted
        try:
            self.set_breakpoints_muted(True)
            # This is about to not work, with my rework of how breakpoint muting works.
            # TODO: figure out a way to set just one temporary breakpoint, with both us and DAP, while muted
            # Make sure it's self-cleaning, the tests will check for this
            self.set_breakpoint(path, line, temporary=True)
            self.resume()
            self.wait_for_pause()
        finally:
            if self.state != SessionState.STOPPED:
                self.set_breakpoints_muted(was_muted)  # restore our muting state

    def set_breakpoint(
        self, path: Path, line: int, temporary: bool = False, condition: str | None = None,
    ) -> Breakpoint:
        """Set a new breakpoint. See the docstring on the `Breakpoints` class to understand why this is so complex."""
        line_text = fetch_line_text(path, line)[:120]
        bp = self.breakpoints.add_breakpoint(path, line, line_text, condition, temporary)
        self.breakpoints.refresh(self.set_breakpoints(self.breakpoints.get_file(path)))
        return bp

    def set_breakpoints(self, file: File) -> Message:
        """
        Send all breakpoints we're currently tracking in the given file, to DAP.
        This wholly replaces all breakpoints in that file, in the DAP server.
        Sadly, this is the *only* operation you can do with breakpoints in DAP, at all.
        Pass in an empty file (with no breakpoints) to remove all breakpoints in that file.
        """
        return self._client.set_breakpoints(str(file.path), [bp.to_dap() for bp in file.list_breakpoints()])

    def set_breakpoints_muted(self, breakpoints_muted: bool):
        """Set all breakpoints to muted."""
        if self.breakpoints_muted == breakpoints_muted:
            return  # already there, nothing to do

        self.breakpoints_muted = breakpoints_muted
        # for every file we have
        for file in self.breakpoints.list_files():
            if self.breakpoints_muted:
                # clear each file by sending a blank version of it
                # DO NOT refresh our breakpoints internally
                self.set_breakpoints(File(file.path))
            else:
                # re-send the real file to DAP if we're unmuting
                # do refresh our breakpoints internally, this changes their IDs
                self.breakpoints.refresh(self.set_breakpoints(file))

    def step(self, direction: StepDirection) -> None:
        """Step into, over, or out of the current thread."""
        self.assert_state(SessionState.PAUSED)
        thread_id = self.threads.get_current_thread_id()
        if direction == StepDirection.INTO:
            self._client.step_in(thread_id)
        elif direction == StepDirection.OVER:
            self._client.next(thread_id)
        elif direction == StepDirection.OUT:
            self._client.step_out(thread_id)
        self.current_position = self.fetch_current_position(thread_id)

    def stop(self) -> None:
        """Stop this session."""
        self._client.disconnect()
        if self.we_own:
            psutil.Process(self.debugee_pid).send_signal(SIGTERM)

    def wait_for_pause(self) -> None:
        """Wait for the debugger to pause on a line on its own. Only blocks, does not send anything to DAP."""
        if self.state == SessionState.PAUSED:
            return  # we are already paused, don't just block forever
        self._client.wait_for_pause()

    # internal state management tools

    def assert_state(self, expected_state: SessionState) -> None:
        """Assert that this session is in the given state. Raises a `SessionStateError` if not."""
        if self.state != expected_state:
            raise SessionStateError(expected_state, self.state)

    def fetch_current_position(self, thread_id: int | None) -> Breakpoint | None:
        """
        Get a floating breakpoint that represents the current position of the thread with the given ID.
        IMPORTANT: On a paused thread, this takes 20ms. On a running thread, it takes 600ms.
        This can be done while running but don't do that unless you have to, it's super slow.
        """
        if thread_id is None:
            return None
        top_frame = self.get_stack_trace(thread_id, limit=1).frames[0]
        return Breakpoint.floating(Path(top_frame.file), top_frame.line)

    def _fetch_variable_children(
        self, variable_id: int, output: list[Variable] | None, show_hidden: bool, depth: int,
    ) -> None:
        """Fetch the children of a variable, into the given output array, recursively, down to the given depth."""
        if depth == 0 or variable_id == 0 or output is None:
            return

        for dap_variable in self._client.variables(variable_id)["body"]["variables"]:
            child = Variable.from_dap(dap_variable)
            # All the variables we want to hide by default, in python, luckily, do not have a type
            if child.type or show_hidden:
                output.append(child)
                self._fetch_variable_children(child.id, child.children, show_hidden, depth - 1)

    def _handle_message(self, message: Message) -> None:
        """
        Handle any state updates that need to happen when we see certain messages.
        This sees every message that the DAP server sends to us, in order.
        """
        body = message.get("body")
        if body is not None and "threadId" in body:
            self.threads.update(message)

        event = message.get("event")
        if event == "stopped":
            self.threads.set_current(body["threadId"])
            if hit_breakpoint_ids := body.get("hitBreakpointIds"):
                bp = self.breakpoints.get_breakpoint_by_id(hit_breakpoint_ids[0])
                bp.hit_count += 1
                self.current_position = bp
                if bp.temporary:
                    self.remove_breakpoint(bp.file, bp.line)

            self.state = SessionState.PAUSED

        if event == "terminated":
            self.state = SessionState.STOPPED
            self.current_position = None  # don't report bad data from a stopped session

        # TODO: handle other passive messages that update our internal model of the debugger's state here
