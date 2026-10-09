from socket import AF_INET, SOCK_STREAM, socket
import subprocess

from exceptions import DebugpyInstallationFailed


def install_debugpy(python_path: str) -> None:
    """
    Make sure the python installation at the given path has debugpy installed.
    Only installs debugpy if it's not already available.
    """
    if subprocess.run([python_path, "-c", "import debugpy"], capture_output=True).returncode == 0:
        return
    install_result = subprocess.run([python_path, "-m", "pip", "install", "debugpy"], capture_output=True)
    if install_result.returncode != 0:
        raise DebugpyInstallationFailed(python_path, install_result.stdout, install_result.stderr)


def find_free_port() -> int:
    """Find a free, high-numbered port on the system."""
    with socket(AF_INET, SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
