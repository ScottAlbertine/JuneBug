import subprocess
import sys

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


async def test_attach_debugger_session(client: Client) -> None:
    port = find_free_port()
    stdout_path = TEMP_DIR / f"{__name__}.test_simple.stdout.txt"
    stderr_path = TEMP_DIR / f"{__name__}.test_simple.stderr.txt"
    debugee = subprocess.Popen(
        args=[
            sys.executable,
            "-Xfrozen_modules=off",
            "-m", "debugpy",
            "--listen", f"{port}",
            "--wait-for-client",
            FAKE_MAIN,
        ],
        stdout=open(stdout_path, "w"),
        stderr=open(stderr_path, "w"),
        cwd=str(PROJECT_ROOT),
    )

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
    assert stdout_path.read_text() == ""
    assert stderr_path.read_text() == ""
