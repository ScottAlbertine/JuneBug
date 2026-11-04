import signal
from subprocess import Popen
import sys
from typing import Iterable

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from constants import TEMP_DIR
from tests.constants import FAKE_MAIN, FAKE_MAIN_MULTI_THREAD, PROJECT_ROOT
from tests.utils import MatchAny
from utils import find_free_port


async def test_launch_debugger_session__invalid(client: Client) -> None:

    with pytest.raises(ToolError, match=r"project_path\n.+Missing required argument"):
        await client.call_tool("attach_debugger_session", {"port": 27385})

    with pytest.raises(ToolError, match=r"project_path must be an absolute directory path\."):
        await client.call_tool("attach_debugger_session", {"project_path": "a/b/c", "port": 27385})

    with pytest.raises(ToolError, match=r"port\n.+Input should be greater than or equal to 0"):
        await client.call_tool("attach_debugger_session", {"project_path": str(PROJECT_ROOT), "port": -1})

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool(
            "attach_debugger_session", {"project_path": str(PROJECT_ROOT), "port": 27385, "timeout": -1},
        )


@pytest.fixture()
def port() -> int:
    """We need a consistent port between the fixture (which launches the debugee) and the test (which connects to it."""
    return find_free_port()


def launch_debugee(port, *args: str) -> Popen[bytes]:
    return Popen(
        args=[sys.executable, "-Xfrozen_modules=off", "-m", "debugpy", "--listen", f"{port}", *args],
        stdout=open(TEMP_DIR / f"{port}.test_simple.stdout.txt", "w"),
        stderr=open(TEMP_DIR / f"{port}.test_simple.stderr.txt", "w"),
        cwd=str(PROJECT_ROOT),
    )

def kill_debugee(pid: int) -> None:
    # Windows doesn't have SIGKILL, we can't even import it
    kill_signal = signal.SIGTERM if sys.platform == "win32" else signal.SIGKILL
    psutil.Process(pid).send_signal(kill_signal)

@pytest.fixture()
def paused_debugee(port: int) -> Iterable[Popen[bytes]]:
    """
    We need to ensure that no matter what happens during the test, we kill the debugee.
    Easiest way to do that is to use a yielding fixture.
    """
    debugee = launch_debugee(port, "--wait-for-client", FAKE_MAIN)
    yield debugee
    kill_debugee(debugee.pid)


@pytest.fixture()
def running_debugee(port: int) -> Iterable[Popen[bytes]]:
    debugee = launch_debugee(port, FAKE_MAIN_MULTI_THREAD)
    yield debugee
    kill_debugee(debugee.pid)


async def test_attach_debugger_session(client: Client, paused_debugee: Popen[bytes], port: int) -> None:
    """Test that we can attach to a paused debugger session."""
    attach_result = await client.call_tool(
        "attach_debugger_session", {"project_path": str(PROJECT_ROOT), "port": port},
    )
    session = attach_result.structured_content
    assert session == {"id": MatchAny(str), "state": "unknown", "breakpoints_muted": False, "current_position": None}

    proc = psutil.Process(paused_debugee.pid)
    assert proc.is_running()
    # Check that stdout and stderr have been created, but not written to.
    # This proves that the files were opened, and that fake_main hasn't actually started yet.
    assert (TEMP_DIR / f"{__name__}.test_simple.stdout.txt").read_text() == ""
    assert (TEMP_DIR / f"{__name__}.test_simple.stderr.txt").read_text() == ""

    # Set a breakpoint
    await client.call_tool(
        "set_breakpoint", {"session_id": session["id"], "file_path": FAKE_MAIN, "line": 7},
    )

    # See that we don't have to assume the process is running or paused, we can wait for that breakpoint to get hit, and it will get hit
    wait_result = await client.call_tool(
        "control_debugger_session", {"session_id": session["id"], "action": "wait_for_pause"},
    )
    assert wait_result.structured_content == {
        "id": session["id"],
        "state": "paused",
        "breakpoints_muted": False,
        "current_position": {
            "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main.py"),
            "line": 7,
            "line_text": '    print("it started", flush=True)\n',
            "temporary": False,
            "hit_count": 1,
        },
    }


async def test_attach_debugger_session__running(client: Client, running_debugee: Popen[bytes], port: int) -> None:
    """There's a special case we can only get into when attaching to a running session, test that here."""
    attach_result = await client.call_tool(
        "attach_debugger_session", {"project_path": str(PROJECT_ROOT), "port": port},
    )
    session = attach_result.structured_content
    assert session == {"id": MatchAny(str), "state": "unknown", "breakpoints_muted": False, "current_position": None}

    proc = psutil.Process(running_debugee.pid)
    assert proc.is_running()

    # Set a breakpoint on a running process before we send configuration_done() to DAP
    await client.call_tool(
        "set_breakpoint", {"session_id": session["id"], "file_path": FAKE_MAIN_MULTI_THREAD, "line": 38},
    )

    # Wait for that breakpoint to get hit, this proves we properly send configuration_done() to DAP if it wasn't sent already
    wait_result = await client.call_tool(
        "control_debugger_session", {"session_id": session["id"], "action": "wait_for_pause"},
    )
    assert wait_result.structured_content == {
        "id": session["id"],
        "state": "paused",
        "breakpoints_muted": False,
        "current_position": {
            "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
            "line": 38,
            "line_text": "        sleep(1)\n",
            "temporary": False,
            "hit_count": 1,
        },
    }
