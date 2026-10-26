from asyncio import StreamReader, StreamWriter, open_connection, sleep
from itertools import islice
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket
import subprocess

from exceptions import DebugpyInstallationFailed, FileNotFound, LineNotFound


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


async def connect_to_port(host: str, port: int) -> tuple[StreamReader, StreamWriter]:
    """
    Repeatedly try to open an asyncio connection to the given port, every 100ms.
    You must wrap this in your own `asyncio.wait_for()` call.
    Returns the connected socket if successful.
    """
    while True:
        try:
            return await open_connection(host, port)
        except OSError:
            await sleep(0.1)


def normalize_file_path(file_path: str | Path, base_path: str | Path | None = None) -> Path:
    """Normalize a file path to a standard absolute Path.

    Handles strings or Path objects, relative paths, absolute paths, paths with ``..`` components, and ``file://`` URLs.

    :param file_path: A file path in any supported format.
    :param base_path: Optional base directory for resolving relative paths.
        If not specified, file_path must be an absolute path.
    :return: A normalized absolute :class:`Path`.
    :raises ValueError: If file_path is not an absolute path.
    """
    if isinstance(file_path, str) and file_path.startswith("file://"):
        file_path = file_path[7:]
    p = Path(file_path)
    if not p.is_absolute():
        if base_path is None:
            raise ValueError("Path must be an absolute path")
        p = Path(base_path) / p
    return p.resolve()


def fetch_line_text(path: Path, line_num: int) -> str:
    """
    Fetch the text of the given line number from the file at the given path.
    Raises our custom exceptions if the file isn't found, or doesn't have that line number.
    """
    try:
        with path.open() as f:
            return next(islice(f, line_num - 1, line_num))
    except FileNotFoundError:
        raise FileNotFound(path)
    except (StopIteration, ValueError):
        raise LineNotFound(path, line_num)
