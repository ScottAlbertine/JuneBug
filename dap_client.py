"""The best python DAP client I can find, sucks. This is a better one."""

from typing import Any, Callable, Iterator

from dap import DAPClient as CrapClient, Event, InitializedEvent
from dap.protocol import ErrorResponse

from breakpoints import File
from exceptions import DAPError, FrameNotFound, SessionStoppedError, ThreadNotFound
from utils import connect_socket


class DAPClient:
    """
    A better DAP client.

    Handles:
        DAP commands in a sane `result = client.some_command(some_options)` format
        The full lifecycle of its own TCP socket
        Automatic DAP initialization handshake on construction
        Passive event handling via a callback
        Error raising
    """
    CHUNK_SIZE = 65536

    def __init__(self, session_id: str, host: str, port: int, timeout: int, handle_event: Callable[[Event], None]):
        """
        Timeout is in milliseconds.
        Every event this client receives from the DAP server, gets passed to `handle_event`, in order.
        """

        self._handle_event = handle_event  # save the callback we're going to need
        self._client = CrapClient(clientID=session_id, clientName="JuneBug", locale="en-US")
        self._sock = connect_socket(host, port, timeout / 1000.0)
        self._socket_closed = False

        # set up the event iterator
        self._event_iterator = self._pull()

        # empty push on a just-created client sends the initialize request
        self._send()
        # pull until we get the InitializedEvent, this blocks until it is received.
        self._pull_until(lambda e: isinstance(e, InitializedEvent))
        # nothing can happen until we attach, let's do that automatically
        self.attach()

    def _send(self) -> None:
        """
        On the CrapClient, none of the DAP command methods like `.set_breakpoint()` actually send any commands to the DAP server,
        nor do they return any data to the caller.
        Instead, they queue up the command to be sent, on an internal queue.
        Thus, you have to manually call this method after every single command method.
        This extracts the data to send, from the internal queue, and actually sends it.
        """
        if self._socket_closed:
            raise SessionStoppedError()
        self._sock.sendall(self._client.send())

    def _pull(self) -> Iterator[Event]:
        """
        An unbounded iterator that returns every event sent by the DAP server.
        This should only ever be called once, in `.__init__()`.
        After that, everyone (even this class) should use `event_iterator`.
        """
        while True:
            yield from self._client.recv(self._sock.recv(self.CHUNK_SIZE))

    def _pull_until(self, matcher: Callable[[Event], bool]) -> Event:
        """Pull events from the DAP client until the given matcher function returns true on an event, then return that event."""
        for event in self._event_iterator:
            print(event.model_dump_json(indent=2))  # for easy logging

            if isinstance(event, ErrorResponse):
                raise DAPError(event)

            self._handle_event(event)

            if event.event == "terminated":
                self._socket_closed = True
                self._sock.close()

            if matcher(event):
                return event

            if self._socket_closed:
                raise SessionStoppedError()

    def attach(self) -> Event:
        """Attach to a running program."""
        # this is a secret option that allows us to see stack frames from libraries
        self._client.attach(justMyCode=False)
        self._send()
        return self._pull_until(lambda e: e.event == "initialized")

    def cancel(self, request_id: int | None = None, progress_id: str | None = None) -> Event:
        """Cancel a request or progress."""
        self._client.cancel(request_id, progress_id)
        self._send()
        return self._pull_until(lambda e: True)

    def configuration_done(self) -> Event:
        """Indicate that configuration is done."""
        self._client.configuration_done()
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "configurationDone")
        # There are extra events returned after this, that we don't handle, the next command will see it

    def continue_execution(self, thread_id: int) -> None:
        """Continue execution. Does not block."""
        self._client.continue_execution(thread_id)
        self._send()

    def disconnect(self) -> Event:
        """Disconnect from the debug adapter."""
        self._client.disconnect()
        self._send()
        return self._pull_until(lambda e: e.event == "terminated")

    def evaluate(self, expression: str, frame_id: int | None = None, **kwargs) -> Event:
        """Evaluate an expression."""
        self._client.evaluate(expression, frame_id, **kwargs)
        self._send()
        return self._pull_until(lambda e: True)

    def launch(self, program: str, **kwargs) -> Event:
        """Launch a program in the debugger."""
        self._client.launch(program, **kwargs)
        self._send()
        return self._pull_until(lambda e: True)

    def next(self, thread_id: int) -> Event:
        """Step to the next line."""
        self._client.next(thread_id)
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "next")

    def pause(self, thread_id: int) -> Event:
        """Pause execution."""
        self._client.pause(thread_id)
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "pause")

    def scopes(self, frame_id: int) -> Event:
        """Get the scopes for a stack frame."""
        self._client.scopes(frame_id)
        self._send()
        try:
            return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "scopes")
        except DAPError as dap_error:
            e = dap_error.event
            if e.command == "scopes" and e.message.startswith("Wrong ID sent from the client"):
                raise FrameNotFound(frame_id)
            raise

    # TODO: back this out a layer, it should take in a string and a list[dict[str, Any]]
    def set_breakpoints(self, file: File) -> Event:
        """Set breakpoints for a file."""
        self._client.set_breakpoints({"path": str(file.path)}, [bp.to_dap() for bp in file.list_breakpoints()])
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "setBreakpoints")

    def set_exception_breakpoints(self, filters: list[str]) -> Event:
        """Set exception breakpoints."""
        self._client.set_exception_breakpoints(filters)
        self._send()
        return self._pull_until(lambda e: True)

    def set_function_breakpoints(self, breakpoints: list[dict[str, Any]]) -> Event:
        """Set function breakpoints."""
        self._client.set_function_breakpoints(breakpoints)
        self._send()
        return self._pull_until(lambda e: True)

    def set_variable(self, variables_reference: int, name: str, value: str) -> Event:
        """Set the value of a variable."""
        self._client.set_variable(variables_reference, name, value)
        self._send()
        return self._pull_until(lambda e: True)

    def source(self, source_reference: int) -> Event:
        """Get the source code."""
        self._client.source(source_reference)
        self._send()
        return self._pull_until(lambda e: True)

    def stack_trace(self, thread_id: int, limit: int | None = None, offset: int | None = None) -> Event:
        """
        Get the stack trace.
        IMPORTANT: On a paused thread, this takes 20ms. On a running thread, it takes 600ms.
        """
        kwargs = {}
        if limit is not None:
            kwargs["levels"] = limit
        if offset is not None:
            kwargs["startFrame"] = offset

        self._client.stack_trace(thread_id, **kwargs)
        self._send()
        try:
            return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "stackTrace")
        except DAPError as dap_error:
            e = dap_error.event
            if e.command == "stackTrace" and e.message.startswith("Wrong ID sent from the client"):
                raise ThreadNotFound(thread_id)
            raise

    def step_in(self, thread_id: int) -> Event:
        """Step into the current line."""
        self._client.step_in(thread_id)
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "stepIn")

    def step_out(self, thread_id: int) -> Event:
        """Step out of the current function."""
        self._client.step_out(thread_id)
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "stepOut")

    def threads(self) -> Event:
        """Get all threads."""
        self._client.threads()
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "threads")

    def variables(self, variables_reference: int) -> Event:
        """Get variables in a scope."""
        self._client.variables(variables_reference)
        self._send()
        return self._pull_until(lambda e: e.event == "response" and e.body["command"] == "variables")

    def wait_for_pause(self) -> Event:
        """Wait for the debugger to pause on a line on its own. Only blocks, does not send anything to DAP."""
        return self._pull_until(lambda e: e.event == "stopped" or e.event == "terminated")
