class DebugpyInstallationFailed(Exception):
    """Special exception to inform the client that we couldn't install debugpy."""

    def __init__(self, python_path: str, stdout: bytes, stderr: bytes):
        super().__init__(
            f"Failed to install debugpy with {python_path}. \n\n Stderr: \n {stderr.decode('utf-8')} \n\n Stdout: \n {stdout.decode('utf-8')} \n",
        )
