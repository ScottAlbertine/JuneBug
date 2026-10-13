from pathlib import Path
from time import sleep

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from tests.constants import FAKE_MAIN, MAIN_THREAD, PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import create_session


# TODO: try setting a breakpoint on every line in fake main, even on lines that don't exist, see what happens, handle all the edge cases
# Try listing them too, to see how they show up after

async def test_set_breakpoint(client: Client) -> None:

    start_response = await create_session(client, file_path=FAKE_MAIN)
    session_id = start_response["id"]
    pid = start_response["debugee_pid"]
    std_out_path = start_response["std_out_path"]

    breakpoint_response = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13},
    )

    assert breakpoint_response.structured_content == {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
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
    threads = await client.call_tool("list_threads", {"session_id": session_id})
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
        match=rf"Error calling tool 'list_threads': DAP Error from command threads: Server\[pid={pid}] disconnected unexpectedly",
    ):
        threads = await client.call_tool("list_threads", {"session_id": session_id})
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
    session_id = (await create_session(client, file_path=file_to_breakpoint))["id"]

    breakpoint_response = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 13},
    )
    assert breakpoint_response.structured_content == {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
        "line": 13,
        "line_text": None,
        "condition": None,
        "temporary": False,
        "suspend_policy": "all",
        "hit_count": 0,
    }
