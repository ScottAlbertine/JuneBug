"""A client for speaking DAP to a debugee process's DAP port."""
from asyncio import CancelledError, StreamReader, StreamWriter
import json
from typing import Any, AsyncGenerator, Awaitable, Callable, Self

from constants import Message
from exceptions import DAPError, FrameNotFound, SessionStoppedError, ThreadNotFound
from utils import connect_to_port
from .parser import DAP_SEPARATOR, parse_messages

MessageHandler = Callable[[Message], Awaitable]


class DAPClient:
    """
    A client for speaking DAP to a debugee process's DAP port.
    Use `DAPClient.create()` to create a new client, do not call `DAPClient()` directly.
    """
    CHUNK_SIZE = 65536

    @classmethod
    async def create(cls, session_id: str, host: str, port: int, handle_message: MessageHandler) -> Self:
        """
        Create a new client, use this instead of the class's constructor.
        Every message this client receives from the DAP server, gets passed to `handle_message`, in order.
        """
        reader, writer = await connect_to_port(host, port)
        client = cls(reader, writer, handle_message)
        await client.initialize(session_id)
        # nothing can happen until we attach, let's do that automatically
        await client.attach()
        return client

    def __init__(self, reader: StreamReader, writer: StreamWriter, handle_message: MessageHandler):
        """DO NOT CALL THIS, this is for internal use only."""

        self._reader = reader
        self._writer = writer
        self._handle_message = handle_message  # save the callback we're going to need
        self._closed = False
        self._seq_counter = 0

        self._exception_breakpoint_filters: list[dict[str, Any]] = []

        # set up the message iterator
        self._message_iterator = self._pull()

    def _make_request(self, command: str, arguments: dict[str, Any] | None = None) -> bytes:
        """Create a DAP request message."""
        content: dict[str, Any] = {"seq": self._seq_counter, "type": "request", "command": command}
        if arguments is not None:
            content["arguments"] = arguments

        encoded_content = json.dumps(content).encode("utf-8")
        headers = f"Content-Length: {len(encoded_content)}".encode("utf-8")
        return headers + DAP_SEPARATOR + encoded_content

    async def _send_request(self, command: str, arguments: dict[str, Any] | None = None) -> None:
        """Send a request to the debug adapter."""

        if self._closed:
            raise SessionStoppedError()
        self._writer.write(self._make_request(command, arguments))
        await self._writer.drain()
        self._seq_counter += 1

    async def _pull(self) -> AsyncGenerator[Message | CancelledError, None]:
        """
        An unbounded iterator that returns every message we receive from the DAP server.
        This should only ever be called once, in `.__init__()`.
        After that, everyone (even this class) should use `_message_iterator`.
        """
        # Used to save data as it comes in from the socket until we have a full message
        buffer = bytearray()
        while True:
            try:
                buffer += await self._reader.read(self.CHUNK_SIZE)
            except CancelledError as exc:
                # we can't raise this exception without breaking out of this loop, which permanently breaks this client
                # so we yield it instead and continue with the loop
                yield exc

            try:
                for message in parse_messages(buffer):
                    yield message
            except Exception:
                # Clear the buffer to prevent further parsing issues
                buffer.clear()

    async def _pull_until(self, matcher: Callable[[Message], bool]) -> Message:
        """ Pull JSON dicts from the DAP client until the given matcher function returns true on a dict, then return that dict. """
        async for message in self._message_iterator:
            # print(message)  # for easy logging

            if isinstance(message, CancelledError):  # this is how timeouts show up
                raise message  # now we're in a loop that's ok to exit, we can raise the error

            if not message.get("success", True):
                raise DAPError(message)

            await self._handle_message(message)

            if message.get("type") == "event" and message.get("event") == "terminated":
                self._closed = True
                self._writer.close()
                await self._writer.wait_closed()

            if matcher(message):
                return message

            if self._closed:
                raise SessionStoppedError()

    async def attach(self) -> Message:
        """Attach to a running program."""
        # this is a secret option that allows us to see stack frames from libraries
        await self._send_request("attach", {"justMyCode": False})
        return await self._pull_until(lambda m: m.get("type") == "event" and m.get("event") == "initialized")

    async def cancel(self, request_id: int | None = None, progress_id: str | None = None) -> Message:
        """Cancel a request or progress."""
        arguments = {}
        if request_id is not None:
            arguments["requestId"] = request_id
        if progress_id is not None:
            arguments["progressId"] = progress_id
        await self._send_request("cancel", arguments)
        return await self._pull_until(lambda m: True)

    async def configuration_done(self) -> Message:
        """Indicate that configuration is done."""
        await self._send_request("configurationDone")
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "configurationDone")
        # There are extra messages returned after this, that we don't handle, the next command will see it

    async def continue_execution(self, thread_id: int) -> None:
        """Continue execution. Does not block."""
        await self._send_request("continue", {"threadId": thread_id})

    async def disconnect(self) -> Message:
        """Disconnect from the debug adapter."""
        await self._send_request("disconnect")
        return await self._pull_until(lambda m: m.get("type") == "event" and m.get("event") == "terminated")

    async def evaluate(self, expression: str, frame_id: int, **kwargs) -> Message:
        """Evaluate an expression."""
        await self._send_request("evaluate", {"expression": expression, "frameId": frame_id, **kwargs})
        try:
            return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "evaluate")
        except DAPError as dap_error:
            m = dap_error.message
            if m.get("command") == "evaluate" and m.get("message", "").startswith("Wrong ID sent from the client"):
                raise FrameNotFound(frame_id)
            raise

    async def initialize(self, session_id: str) -> Message:
        await self._send_request(
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
        initialize_response = await self._pull_until(
            lambda m: m.get("type") == "response" and m.get("command") == "initialize",
        )
        self._exception_breakpoint_filters = initialize_response.get("body", {}).get("exceptionBreakpointFilters", [])
        return initialize_response

    async def launch(self, program: str, **kwargs) -> Message:
        """Launch a program in the debugger."""
        await self._send_request("launch", {"program": program, **kwargs})
        return await self._pull_until(lambda m: True)

    async def next(self, thread_id: int) -> Message:
        """Step to the next line."""
        await self._send_request("next", {"threadId": thread_id})
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "next")

    async def pause(self, thread_id: int) -> Message:
        """Pause execution."""
        await self._send_request("pause", {"threadId": thread_id})
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "pause")

    async def scopes(self, frame_id: int) -> Message:
        """Get the scopes for a stack frame."""
        await self._send_request(command="scopes", arguments={"frameId": frame_id})
        try:
            return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "scopes")
        except DAPError as dap_error:
            m = dap_error.message
            if m.get("command") == "scopes" and m.get("message", "").startswith("Wrong ID sent from the client"):
                raise FrameNotFound(frame_id)
            raise

    async def set_breakpoints(self, path: str, breakpoints: list[dict[str, Any]]) -> Message:
        """Set breakpoints for a file."""
        await self._send_request("setBreakpoints", {"source": {"path": path}, "breakpoints": breakpoints})
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "setBreakpoints")

    async def set_exception_breakpoints(self, filters: list[str]) -> Message:
        """Set exception breakpoints."""
        await self._send_request("setExceptionBreakpoints", {"filters": filters})
        return await self._pull_until(
            lambda m: m.get("type") == "response" and m.get("command") == "setExceptionBreakpoints",
        )

    async def set_function_breakpoints(self, breakpoints: list[dict[str, Any]]) -> Message:
        """Set function breakpoints."""
        await self._send_request("setFunctionBreakpoints", {"breakpoints": breakpoints})
        return await self._pull_until(lambda m: True)

    async def set_variable(self, variables_reference: int, name: str, value: str) -> Message:
        """Set the value of a variable."""
        await self._send_request(
            "setVariable", {"variablesReference": variables_reference, "name": name, "value": value},
        )
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "setVariable")

    async def source(self, source_reference: int) -> Message:
        """Get the source code."""
        await self._send_request("source", {"sourceReference": source_reference})
        return await self._pull_until(lambda m: True)

    async def stack_trace(self, thread_id: int, limit: int | None = None, offset: int | None = None) -> Message:
        """
        Get the stack trace.
        IMPORTANT: On a paused thread, this takes 20ms. On a running thread, it takes 600ms.
        """
        arguments = {"threadId": thread_id}
        if limit is not None:
            arguments["levels"] = limit
        if offset is not None:
            arguments["startFrame"] = offset

        await self._send_request("stackTrace", arguments)
        try:
            return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "stackTrace")
        except DAPError as dap_error:
            m = dap_error.message
            if m.get("command") == "stackTrace" and m.get("message", "").startswith("Wrong ID sent from the client"):
                raise ThreadNotFound(thread_id)
            raise

    async def step_in(self, thread_id: int) -> Message:
        """Step into the current line."""
        await self._send_request("stepIn", {"threadId": thread_id})
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "stepIn")

    async def step_out(self, thread_id: int) -> Message:
        """Step out of the current function."""
        await self._send_request("stepOut", {"threadId": thread_id})
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "stepOut")

    async def threads(self) -> Message:
        """Get all threads."""
        await self._send_request("threads")
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "threads")

    async def variables(self, variables_reference: int, **kwargs) -> Message:
        """Get variables in a scope."""
        await self._send_request("variables", {"variablesReference": variables_reference, **kwargs})
        return await self._pull_until(lambda m: m.get("type") == "response" and m.get("command") == "variables")

    async def wait_for_pause(self) -> Message:
        """Wait for the debugger to pause on a line on its own. Only blocks, does not send anything to DAP."""
        return await self._pull_until(
            lambda m: m.get("type") == "event" and (m.get("event") == "stopped" or m.get("event") == "terminated"),
        )
