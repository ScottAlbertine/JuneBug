from pathlib import Path
import sys
from time import sleep

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import MAIN_THREAD


async def test_set_breakpoint(client: Client) -> None:
    file_to_breakpoint = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))

    session_start = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )
    start_response = session_start.structured_content
    session_id = start_response["id"]
    pid = start_response["debugee_pid"]
    std_out_path = start_response["std_out_path"]

    breakpoint_response = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 13},
    )

    assert breakpoint_response.structured_content == {
        "id": 0,
        "type": "line",
        "file": "/Users/scott/Repos/JuneBug/tests/fakes/fake_main.py",
        "line": 13,
        "line_text": None,
        "condition": None,
        "temporary": False,
        "suspend_policy": "all",
        "hit_count": 0,
    }

    # check that the breakpoint was set, by hitting it.
    wait_for_pause = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "wait_for_pause"},
    )
    assert wait_for_pause.structured_content["state"] == "paused"

    # check that the breakpoint was hit, based on thread state, stdout, and pid existence
    threads = await client.call_tool("get_threads", {"session_id": session_id})
    assert threads.structured_content == {'threads': [MAIN_THREAD], 'total_count': 1}
    assert Path(std_out_path).read_text() == "it started\n"
    assert psutil.Process(pid).is_running()

    # resume again
    resume_2 = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "resume"},
    )
    assert resume_2.structured_content["state"] == "running"

    sleep(1)

    # Check that the program has run to completion, based on thread state, stdout, and pid existence
    with pytest.raises(
        ToolError,
        match=rf"Error calling tool 'get_threads': DAP Error from command threads: Server\[pid={pid}] disconnected unexpectedly",
    ):
        threads = await client.call_tool("get_threads", {"session_id": session_id})
        assert threads.structured_content == {'threads': [MAIN_THREAD], 'total_count': 1}
    assert Path(std_out_path).read_text() == "it started\nit finished\n"
    assert psutil.Process(pid).status() == psutil.STATUS_ZOMBIE


@pytest.mark.parametrize(
    ["file_to_breakpoint"],
    [
        (str(Path(fake_main.__file__).resolve()),),
        (str(Path(fake_main.__file__).resolve()) + "/../fake_main.py",),
        ("file://" + str(Path(fake_main.__file__).resolve()),),
    ],
)
async def test_set_breakpoint__odd_file_paths(client: Client, file_to_breakpoint: str) -> None:
    """Test non-standard, aka non-relative paths to the file to breakpoint"""
    session_start = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )
    session_id = session_start.structured_content["id"]

    breakpoint_response = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 13},
    )
    assert breakpoint_response.structured_content == {
        "id": 0,
        "type": "line",
        "file": "/Users/scott/Repos/JuneBug/tests/fakes/fake_main.py",
        "line": 13,
        "line_text": None,
        "condition": None,
        "temporary": False,
        "suspend_policy": "all",
        "hit_count": 0,
    }
