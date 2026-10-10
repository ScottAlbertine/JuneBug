from dap.protocol import ErrorResponse


class DebugpyInstallationFailed(Exception):
    """Special exception to inform the client that we couldn't install debugpy."""

    def __init__(self, python_path: str, stdout: bytes, stderr: bytes):
        super().__init__(
            f"Failed to install debugpy with {python_path}. \n\n Stderr: \n {stderr.decode('utf-8')} \n\n Stdout: \n {stdout.decode('utf-8')} \n",
        )

class DAPError(Exception):
    """Generic exception representing an `ErrorResponse` from the DAP client."""

    def __init__(self, error: ErrorResponse):
        super().__init__(f"DAP Error from command {error.command}: {error.message}")

class MissingSessionId(Exception):
    """Exception indicating that you need to specify a session ID."""

    def __init__(self):
        super().__init__("Session ID is required for this tool call, and you did not specify a session ID.")


class SessionNotFound(Exception):
    """Exception indicating that the client tried to interact with a debug session that was not found."""

    def __init__(self, client_id: str):
        super().__init__(f"Session {client_id} was not found.")
