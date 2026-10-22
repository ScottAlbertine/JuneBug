from pathlib import Path

from constants import Message
from enums import SessionState


class AbsolutePathError(Exception):
    """Exception indicating that the given field must be an absolute directory path."""

    def __init__(self, field_name: str):
        super().__init__(f"{field_name} must be an absolute directory path.")


class DAPError(Exception):
    """Generic exception representing an `ErrorResponse` from the DAP client."""

    def __init__(self, message: Message):
        self.message = message
        command = message.get("command")
        error_message = message.get("message")
        super().__init__(f"DAP Error from command {command}: {error_message}")


class DebugpyInstallationFailed(Exception):
    """Special exception to inform the client that we couldn't install debugpy."""

    def __init__(self, python_path: str, stdout: bytes, stderr: bytes):
        super().__init__(
            f"Failed to install debugpy with {python_path}. \n\n Stderr: \n {stderr.decode('utf-8')} \n\n Stdout: \n {stdout.decode('utf-8')} \n",
        )


class DirectoryNotFound(Exception):
    """Exception indicating that the client's specified directory was not found."""

    def __init__(self, path: str | Path):
        super().__init__(f"Directory {path} was not found.")


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
        super().__init__(
            "There is more than one active session, and you did not specify a session ID. You must specify one.",
        )


class SessionNotFound(Exception):
    """Exception indicating that the client tried to interact with a debug session that was not found."""

    def __init__(self, client_id: str):
        super().__init__(f"Session {client_id} was not found.")


class SessionStateError(Exception):
    """Exception indicating that the specified debug session is in the wrong state for what you're trying to do."""

    def __init__(self, expected_state: SessionState, actual_state: SessionState):
        super().__init__(
            f"Session must be {expected_state.value} to call that tool. Session is currently {actual_state.value}.",
        )


class SessionStoppedError(Exception):
    """Exception indicating that the client tried to interact with a debug session that has terminated."""

    def __init__(self):
        super().__init__("Session has stopped, no more tool calls can be made to its id. Start a new session instead.")


class ThreadNotFound(Exception):
    """Exception indicating that the client's specified thread was not found."""

    def __init__(self, thread_id: int):
        super().__init__(f"Thread {thread_id} was not found.")
