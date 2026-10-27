from signal import SIGKILL
from subprocess import Popen
import sys
from typing import Iterable

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from constants import TEMP_DIR
from tests.constants import FAKE_MAIN, PROJECT_ROOT
from tests.utils import MatchAny
from utils import find_free_port


async def test_launch_debugger_session__invalid(client: Client) -> None:

    with pytest.raises(ToolError, match=r"project_path\n.+Missing required argument.+"):
        await client.call_tool("attach_debugger_session", {"port": 27385})

    with pytest.raises(ToolError, match=r"project_path must be an absolute directory path\."):
        await client.call_tool("attach_debugger_session", {"project_path": "a/b/c", "port": 27385})

    with pytest.raises(ToolError, match=r"port\n.+Input should be greater than or equal to 0.+"):
        await client.call_tool("attach_debugger_session", {"project_path": str(PROJECT_ROOT), "port": -1})

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0.+"):
        await client.call_tool(
            "attach_debugger_session", {"project_path": str(PROJECT_ROOT), "port": 27385, "timeout": -1},
        )


@pytest.fixture()
def port() -> int:
    """We need a consistent port between the fixture (which launches the debugee) and the test (which connects to it."""
    return find_free_port()


@pytest.fixture()
def debugee(port: int) -> Iterable[Popen[bytes]]:
    """
    We need to ensure that no matter what happens during the test, we kill the debugee.
    Easiest way to do that is to use a yielding fixture.
    """
    debugee = Popen(
        args=[
            sys.executable,
            "-Xfrozen_modules=off",
            "-m", "debugpy",
            "--listen", f"{port}",
            "--wait-for-client",
            FAKE_MAIN,
        ],
        stdout=open(TEMP_DIR / f"{__name__}.test_simple.stdout.txt", "w"),
        stderr=open(TEMP_DIR / f"{__name__}.test_simple.stderr.txt", "w"),
        cwd=str(PROJECT_ROOT),
    )
    yield debugee
    psutil.Process(debugee.pid).send_signal(SIGKILL)


async def test_attach_debugger_session(client: Client, debugee: Popen[bytes], port: int) -> None:
    create_result = await client.call_tool(
        "attach_debugger_session", {"project_path": str(PROJECT_ROOT), "port": port},
    )

    assert create_result.structured_content == {
        "id": MatchAny(str), "state": "unknown", "breakpoints_muted": False, "current_position": None,
    }

    proc = psutil.Process(debugee.pid)
    assert proc.is_running()
    # Check that stdout and stderr have been created, but not written to.
    # This proves that the files were opened, and that fake_main hasn't actually started yet.
    assert (TEMP_DIR / f"{__name__}.test_simple.stdout.txt").read_text() == ""
    assert (TEMP_DIR / f"{__name__}.test_simple.stderr.txt").read_text() == ""
