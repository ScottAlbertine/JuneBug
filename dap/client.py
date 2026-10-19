"""A client for speaking DAP to a debugee process's DAP port."""
import json
from typing import Any, Callable, Iterator

from constants import Message
from exceptions import DAPError, FrameNotFound, SessionStoppedError, ThreadNotFound
from utils import connect_socket
from .parser import DAP_SEPARATOR, parse_messages


class DAPClient:
    """A client for speaking DAP to a debugee process's DAP port."""
    CHUNK_SIZE = 65536

    def __init__(self, session_id: str, host: str, port: int, timeout: int, handle_message: Callable[[Message], None]):
        """
        Timeout is in milliseconds.
        Every message this client receives from the DAP server, gets passed to `handle_message`, in order.
        """

        self._handle_message = handle_message  # save the callback we're going to need
        self._sock = connect_socket(host, port, timeout / 1000.0)
        self._socket_closed = False
        self._seq_counter = 0

        # set up the message iterator
        self._message_iterator = self._pull()

        self._send_request(
            "initialize",
            {
                "clientID": session_id,
                "clientName": "JuneBug",
                "locale": "en-US",
                "adapterID": None,
                "linesStartAt1": True,
                "columnsStartAt1": True,
                "pathFormat": "path",
                # "supportsVariableType": supportsVariableType,
                # "supportsVariablePaging": supportsVariablePaging,
                # "supportsRunInTerminalRequest": supportsRunInTerminalRequest,
                # "supportsMemoryReferences": supportsMemoryReferences,
                # "supportsProgressReporting": supportsProgressReporting,
                # "supportsInvalidatedEvent": supportsInvalidatedEvent,
                # "supportsMemoryEvent": supportsMemoryEvent,
            },
        )
        # pull until we get the initialize response, this blocks until it is received.
        initialize_response = self._pull_until(
            lambda m: m.get("type") == "response" and m.get("command") == "initialize",
        )

        initialize_body = initialize_response.get("body", {})
        self.exception_breakpoint_filters: list[dict[str, Any]] = initialize_body.get("exceptionBreakpointFilters", [])

        # nothing can happen until we attach, let's do that automatically
        self.attach()

    def _make_request(self, command: str, arguments: dict[str, Any] | None = None) -> bytes:
        """Create a DAP request message."""
        content: dict[str, Any] = {"seq": self._seq_counter, "type": "request", "command": command}
        if arguments is not None:
            content["arguments"] = arguments

        encoded_content = json.dumps(content).encode("utf-8")
        headers = f"Content-Length: {len(encoded_content)}".encode("utf-8")
        return headers + DAP_SEPARATOR + encoded_content

    def _send_request(self, command: str, arguments: dict[str, Any] | None = None) -> None:
        """Send a request to the debug adapter."""

        if self._socket_closed:
            raise SessionStoppedError()
        self._sock.sendall(self._make_request(command, arguments))
        self._seq_counter += 1

    def _pull(self) -> Iterator[Message]:
        """
        An unbounded iterator that returns every message we receive from the DAP server.
        This should only ever be called once, in `.__init__()`.
        After that, everyone (even this class) should use `_message_iterator`.
        """
        # Used to save data as it comes in from the socket until we have a full message
        buffer = bytearray()
        while True:
            buffer += self._sock.recv(self.CHUNK_SIZE)
            try:
                yield from parse_messages(buffer)
            except Exception:
                # Clear the buffer to prevent further parsing issues
                buffer.clear()

    def _pull_until(self, matcher: Callable[[Message], bool]) -> Message:
        """ Pull JSON dicts from the DAP client until the given matcher function returns true on a dict, then return that dict. """
        for message in self._message_iterator:
            print(message)  # for easy logging

            if not message.get("success", True):
                raise DAPError(message)

            self._handle_message(message)

            if message.get("type") == "event" and message.get("event") == "terminated":
                self._socket_closed = True
                self._sock.close()

            if matcher(message):
                return message

            if self._socket_closed:
                raise SessionStoppedError()

    def attach(self) -> Message:
        """Attach to a running program."""
        # this is a secret option that allows us to see stack frames from libraries
        self._send_request("attach", {"justMyCode": False})
        return self._pull_until(lambda m: m.get("type") == "event" and m.get("event") == "initialized")

    def cancel(self, request_id: int | None = None, progress_id: str | None = None) -> Message:
        """Cancel a request or progress."""
        arguments = {}
        if request_id is not None:
            arguments["requestId"] = request_id
        if progress_id is not None:
            arguments["progressId"] = progress_id
        self._send_request("cancel", arguments)
        return self._pull_until(lambda m: True)

    def configuration_done(self) -> Message:
        """Indicate that configuration is done."""
        self._send_request("configurationDone")
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "configurationDone")
        # There are extra messages returned after this, that we don't handle, the next command will see it

    def continue_execution(self, thread_id: int) -> None:
        """Continue execution. Does not block."""
        self._send_request("continue", {"threadId": thread_id})

    def disconnect(self) -> Message:
        """Disconnect from the debug adapter."""
        self._send_request("disconnect")
        return self._pull_until(lambda m: m.get("type") == "event" and m.get("event") == "terminated")

    def evaluate(self, expression: str, frame_id: int | None = None, **kwargs) -> Message:
        """Evaluate an expression."""
        arguments = {"expression": expression, **kwargs}
        if frame_id is not None:
            arguments["frameId"] = frame_id
        self._send_request("evaluate", arguments)
        return self._pull_until(lambda m: True)

    def launch(self, program: str, **kwargs) -> Message:
        """Launch a program in the debugger."""
        self._send_request("launch", {"program": program, **kwargs})
        return self._pull_until(lambda m: True)

    def next(self, thread_id: int) -> Message:
        """Step to the next line."""
        self._send_request("next", {"threadId": thread_id})
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "next")

    def pause(self, thread_id: int) -> Message:
        """Pause execution."""
        self._send_request("pause", {"threadId": thread_id})
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "pause")

    def scopes(self, frame_id: int) -> Message:
        """Get the scopes for a stack frame."""
        self._send_request(command="scopes", arguments={"frameId": frame_id})
        try:
            return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "scopes")
        except DAPError as dap_error:
            m = dap_error.message
            if m.get("command") == "scopes" and m.get("message", "").startswith("Wrong ID sent from the client"):
                raise FrameNotFound(frame_id)
            raise

    def set_breakpoints(self, path: str, breakpoints: list[dict[str, Any]]) -> Message:
        """Set breakpoints for a file."""
        self._send_request("setBreakpoints", {"source": {"path": path}, "breakpoints": breakpoints})
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "setBreakpoints")

    def set_exception_breakpoints(self, filters: list[str]) -> Message:
        """Set exception breakpoints."""
        self._send_request("setExceptionBreakpoints", {"filters": filters})
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "setExceptionBreakpoints")

    def set_function_breakpoints(self, breakpoints: list[dict[str, Any]]) -> Message:
        """Set function breakpoints."""
        self._send_request("setFunctionBreakpoints", {"breakpoints": breakpoints})
        return self._pull_until(lambda m: True)

    def set_variable(self, variables_reference: int, name: str, value: str) -> Message:
        """Set the value of a variable."""
        self._send_request(
            "setVariable", {"variablesReference": variables_reference, "name": name, "value": value},
        )
        return self._pull_until(lambda m: True)

    def source(self, source_reference: int) -> Message:
        """Get the source code."""
        self._send_request("source", {"sourceReference": source_reference})
        return self._pull_until(lambda m: True)

    def stack_trace(self, thread_id: int, limit: int | None = None, offset: int | None = None) -> Message:
        """
        Get the stack trace.
        IMPORTANT: On a paused thread, this takes 20ms. On a running thread, it takes 600ms.
        """
        arguments = {"threadId": thread_id}
        if limit is not None:
            arguments["levels"] = limit
        if offset is not None:
            arguments["startFrame"] = offset

        self._send_request("stackTrace", arguments)
        try:
            return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "stackTrace")
        except DAPError as dap_error:
            m = dap_error.message
            if m.get("command") == "stackTrace" and m.get("message", "").startswith("Wrong ID sent from the client"):
                raise ThreadNotFound(thread_id)
            raise

    def step_in(self, thread_id: int) -> Message:
        """Step into the current line."""
        self._send_request("stepIn", {"threadId": thread_id})
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "stepIn")

    def step_out(self, thread_id: int) -> Message:
        """Step out of the current function."""
        self._send_request("stepOut", {"threadId": thread_id})
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "stepOut")

    def threads(self) -> Message:
        """Get all threads."""
        self._send_request("threads")
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "threads")

    def variables(self, variables_reference: int, **kwargs) -> Message:
        """Get variables in a scope."""
        self._send_request("variables", {"variablesReference": variables_reference, **kwargs})
        return self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "variables")

    def wait_for_pause(self) -> Message:
        """Wait for the debugger to pause on a line on its own. Only blocks, does not send anything to DAP."""
        return self._pull_until(
            lambda m: m.get("type") == "event" and (m.get("event") == "stopped" or m.get("event") == "terminated"),
        )
