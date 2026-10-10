"""A debug session, equivalent to a debugger instance like a `pdb` process or a PyCharm debugger tab."""
from typing import Any, Callable, Iterator

from dap import DAPClient, Event, InitializedEvent
from dap.protocol import ErrorResponse

from constants import TEMP_DIR
from enums import DebuggerState
from exceptions import DAPError
from models import SessionStatus, Thread
from threads import Threads
from utils import connect_to_port


class Session:
    """A DAP client that actually connects to a socket and sends/receives messages in a useful manner."""
    CHUNK_SIZE = 65536

    # TODO: handle closing the socket when we need to, not sure when that is, figure it out

    # def __exit__(self, exc_type, exc_val, traceback) -> None:
    #     self.sock.__exit__(exc_type, exc_val, traceback)

    def __init__(
        self, session_id: str, project_path: str, port: int, timeout: int, we_own: bool, pid: int | None = None,
    ):
        """Timeout is in milliseconds."""
        self.breakpoints_muted: bool = False
        self.client = DAPClient(clientID=session_id, clientName="JuneBug", locale="en-US")
        self.current_position = None  # TODO: track this
        self.debugee_pid = pid
        self.has_configuration_done = False
        self.project_path = project_path
        self.session_id = session_id
        self.sock = connect_to_port(port, timeout / 1000.0)
        self.state: DebuggerState = DebuggerState.PAUSED
        self.std_out_path = str(TEMP_DIR / f"{session_id}.stdout.txt") if we_own else None
        self.std_err_path = str(TEMP_DIR / f"{session_id}.stderr.txt") if we_own else None
        self.threads = Threads()

        self.sock.settimeout(30)  # TODO: make this configurable?

        # set up the event iterator
        self._event_iterator = self._pull()

        # empty push on a just-created client sends the initialize request
        self._send()
        # pull until we get the InitializedEvent, this blocks until it is received.
        self._pull_until(lambda e: isinstance(e, InitializedEvent))
        # nothing can happen until we attach, let's do that automatically
        self._attach()
        # always get the initial registry of threads at this point, because we can.
        self.get_threads()

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
        print(event.model_dump_json(indent=2))  # for easy logging
        if event.event == "thread" and "threadId" in event.body:
            self.threads.update(event)

        # TODO: handle other passive events that update our internal model of the debugger's state here

    def _send(self):
        self.sock.sendall(self.client.send())

    def get_status(self) -> SessionStatus:
        """Get the status of this session."""
        return SessionStatus(
            id=self.session_id,
            state=self.state,
            debugee_pid=self.debugee_pid,
            std_out_path=self.std_out_path,
            std_err_path=self.std_err_path,
            breakpoints_muted=self.breakpoints_muted,
            current_position=self.current_position,
        )

    def pause(self):
        """Pause all threads in this session."""
        for thread in self.get_threads():
            self._pause(thread.id)

    def resume(self):
        """Resume this session."""
        if not self.has_configuration_done:
            # this has to happen once per session, and only once, and it automatically resumes all threads
            self._configuration_done()
            self.has_configuration_done = True
        else:
            for thread in self.get_threads():
                self._continue_execution(thread.id)
        self.state = DebuggerState.RUNNING

    def get_threads(self) -> list[Thread]:
        """Get all threads, sorted by id."""
        return self.threads.refresh(self._fetch_threads())

    # DAP commands

    def _attach(self) -> Event:
        """Attach to a running program."""
        self.client.attach(a="b")  # the underlying client errors if you don't specify kwargs here.
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
        """Continue execution."""
        self.client.continue_execution(thread_id)
        self._send()

    def _disconnect(self) -> Event:
        """Disconnect from the debug adapter."""
        self.client.disconnect()
        self._send()
        return self._pull_until(lambda e: True)

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
        return self._pull_until(lambda e: True)

    def _scopes(self, frame_id: int) -> Event:
        """Get the scopes for a stack frame."""
        self.client.scopes(frame_id)
        self._send()
        return self._pull_until(lambda e: True)

    def _set_breakpoints(self, source: dict[str, Any], breakpoints: list[dict[str, Any]]) -> Event:
        """Set breakpoints for a source."""
        self.client.set_breakpoints(source, breakpoints)
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

    def _stack_trace(self, thread_id: int, **kwargs) -> Event:
        """Get the stack trace."""
        self.client.stack_trace(thread_id, **kwargs)
        self._send()
        return self._pull_until(lambda e: True)

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

    def _variables(self, variables_reference: int, **kwargs) -> Event:
        """Get variables in a scope."""
        self.client.variables(variables_reference, **kwargs)
        self._send()
        return self._pull_until(lambda e: True)
