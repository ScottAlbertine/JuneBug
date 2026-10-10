from socket import AF_INET, SOCK_STREAM, socket
import subprocess
from time import sleep, time

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


def connect_to_port(port: int, timeout: float) -> socket:
    """
    Try to connect a socket to the given port, every 100ms for up to `timeout` seconds total.
    Returns the connected socket if successful.
    Raises TimeoutError if the timeout is reached.
    Create a socket, connect it to the given port, retrying every 100ms, for up to `timeout` seconds total.
    No idea why socket.connnect() doesn't do this out of the box, but here we are.
    """

    start_time = time()
    while time() - start_time < timeout:
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect(("127.0.0.1", port))
            return sock
        except ConnectionRefusedError:
            sleep(0.1)

    raise TimeoutError()
