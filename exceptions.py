from pathlib import Path

from dap.protocol import ErrorResponse

from enums import DebuggerState


class DebugpyInstallationFailed(Exception):
    """Special exception to inform the client that we couldn't install debugpy."""

    def __init__(self, python_path: str, stdout: bytes, stderr: bytes):
        super().__init__(
            f"Failed to install debugpy with {python_path}. \n\n Stderr: \n {stderr.decode('utf-8')} \n\n Stdout: \n {stdout.decode('utf-8')} \n",
        )


class DAPError(Exception):
    """Generic exception representing an `ErrorResponse` from the DAP client."""

    def __init__(self, event: ErrorResponse):
        self.event = event
        super().__init__(f"DAP Error from command {event.command}: {event.message}")


class FileNotFound(Exception):
    """Exception indicating that the client's specified file was not found."""

    def __init__(self, path: Path):
        super().__init__(f"File {path.resolve()} was not found.")


class FrameNotFound(Exception):
    """Exception indicating that the client's specified frame was not found."""

    def __init__(self, frame_id: int):
        super().__init__(f"Stack frame {frame_id} was not found.")


class LineNotFound(Exception):
    """Exception indicating that the client's specified line was not found."""

    def __init__(self, path: Path, line: int):
        super().__init__(f"Line {line} was not found in {path.resolve()}")


class MissingSessionId(Exception):
    """Exception indicating that you need to specify a session ID."""

    def __init__(self):
        super().__init__("Session ID is required for this tool call, and you did not specify a session ID.")


class SessionNotFound(Exception):
    """Exception indicating that the client tried to interact with a debug session that was not found."""

    def __init__(self, client_id: str):
        super().__init__(f"Session {client_id} was not found.")


class SessionStateError(Exception):
    """Exception indicating that the specified debug session is in the wrong state for what you're trying to do."""

    def __init__(self, expected_state: DebuggerState, actual_state: DebuggerState):
        super().__init__(
            f"Session must be {expected_state.value} to call that tool. Session is currently {actual_state.value}.",
        )


class ThreadNotFound(Exception):
    """Exception indicating that the client's specified thread was not found."""

    def __init__(self, thread_id: int):
        super().__init__(f"Thread {thread_id} was not found.")
