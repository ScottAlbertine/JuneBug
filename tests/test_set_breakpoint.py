from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from tests.constants import FAKE_MAIN, FAKE_MAIN_WITH_LOOP, MAIN_THREAD, PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import create_session, eventual_assert, move_to_next_breakpoint


async def test_set_breakpoint__invalid(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    with pytest.raises(ToolError, match=r"File /definitely/not/a/real/file\.py was not found\."):
        await client.call_tool(
            "set_breakpoint", {"session_id": session_id, "file_path": "/definitely/not/a/real/file.py", "line": 1},
        )

    with pytest.raises(ToolError, match=rf"Line -1 was not found in {PROJECT_ROOT}/tests/fakes/fake_main\.py"):
        await client.call_tool("set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": -1})

    with pytest.raises(ToolError, match=rf"Line 999 was not found in {PROJECT_ROOT}/tests/fakes/fake_main\.py"):
        await client.call_tool("set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 999})


async def test_set_breakpoint(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN)
    session_id = start_response["id"]
    pid = start_response["debugee_pid"]
    std_out_path = start_response["std_out_path"]

    breakpoint_response = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13},
    )

    assert breakpoint_response.structured_content == {
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
        "line": 13,
        "line_text": '    print("it finished", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
    }

    # check that the breakpoint was set, by hitting it.
    wait_for_pause = await move_to_next_breakpoint(client, session_id)
    assert wait_for_pause["state"] == "paused"

    # check that the breakpoint was hit, based on thread state, stdout, and pid existence
    threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}
    assert Path(std_out_path).read_text() == "it started\n"
    assert psutil.Process(pid).is_running()

    # resume again, wait until it stopped
    wait_for_pause = await move_to_next_breakpoint(client, session_id)
    assert wait_for_pause["state"] == "stopped"

    # Check that the program has run to completion, based on thread state, stdout, and process status
    with pytest.raises(
        ToolError, match=r"Session has stopped, no more tool calls can be made to its id\. Start a new session instead\.",
    ):
        threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}
    assert Path(std_out_path).read_text() == "it started\nit finished\n"

    # the process can take a while to change its status, give it 3 seconds to do so
    async def process_exited() -> bool:
        return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE

    await eventual_assert(process_exited, otherwise="Process did not exit within 3 seconds")


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
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
        "line": 13,
        "line_text": '    print("it finished", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
    }


async def test_set_breakpoint__temporary(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN_WITH_LOOP)
    session_id = start_response["id"]
    std_out_path = start_response["std_out_path"]

    bp = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_LOOP, "line": 5, "temporary": True},
    )

    expected_breakpoint = {
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_loop.py",
        "line": 5,
        "line_text": '        print(f"loop number {i}", flush=True)\n',
        "temporary": True,
        "hit_count": 0,
    }

    assert bp.structured_content == expected_breakpoint

    wait_for_pause = await move_to_next_breakpoint(client, session_id)
    expected_breakpoint["hit_count"] += 1
    assert wait_for_pause["current_position"] == expected_breakpoint

    wait_for_done = await move_to_next_breakpoint(client, session_id)
    assert wait_for_done["state"] == "stopped"
    assert wait_for_done["current_position"] is None

    assert Path(std_out_path).read_text() == (
        "it started\nloop number 0\nloop number 1\nloop number 2\nloop number 3\nloop number 4\nit finished\n"
    )


async def test_set_breakpoint__conditional(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN_WITH_LOOP)
    session_id = start_response["id"]
    std_out_path = start_response["std_out_path"]

    bp = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_LOOP, "line": 5, "condition": "i > 2"},
    )

    expected_breakpoint = {
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_loop.py",
        "line": 5,
        "line_text": '        print(f"loop number {i}", flush=True)\n',
        "condition": "i > 2",
        "temporary": False,
        "hit_count": 0,
    }

    assert bp.structured_content == expected_breakpoint

    wait_for_pause_1 = await move_to_next_breakpoint(client, session_id)
    expected_breakpoint["hit_count"] += 1
    assert wait_for_pause_1["current_position"] == expected_breakpoint

    # Check that the condition was respected, and that we didn't hit it until i > 2
    variables = await client.call_tool("list_variables", {"session_id": session_id})
    assert variables.structured_content == {
        "variables": [{"name": "i", "type": "int", "evaluate_name": "i", "value": "3", "children": None}],
    }
    assert Path(std_out_path).read_text() == "it started\nloop number 0\nloop number 1\nloop number 2\n"

    # Hit it again, to check that it keeps applying
    wait_for_pause_2 = await move_to_next_breakpoint(client, session_id)
    expected_breakpoint["hit_count"] += 1
    assert wait_for_pause_2["current_position"] == expected_breakpoint
    assert Path(std_out_path).read_text() == "it started\nloop number 0\nloop number 1\nloop number 2\nloop number 3\n"


async def test_set_breakpoint__temporary_conditional(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN_WITH_LOOP)
    session_id = start_response["id"]
    std_out_path = start_response["std_out_path"]

    bp = await client.call_tool(
        "set_breakpoint", {
            "session_id": session_id,
            "file_path": FAKE_MAIN_WITH_LOOP,
            "line": 5,
            "condition": "i > 2",
            "temporary": True,
        },
    )

    expected_breakpoint = {
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_loop.py",
        "line": 5,
        "line_text": '        print(f"loop number {i}", flush=True)\n',
        "condition": "i > 2",
        "temporary": True,
        "hit_count": 0,
    }

    assert bp.structured_content == expected_breakpoint

    wait_for_pause_1 = await move_to_next_breakpoint(client, session_id)
    expected_breakpoint["hit_count"] += 1
    assert wait_for_pause_1["current_position"] == expected_breakpoint

    # Check that the condition was respected, and that we didn't hit it until i > 2
    variables = await client.call_tool("list_variables", {"session_id": session_id})
    assert variables.structured_content == {
        "variables": [{"name": "i", "type": "int", "evaluate_name": "i", "value": "3", "children": None}],
    }
    assert Path(std_out_path).read_text() == "it started\nloop number 0\nloop number 1\nloop number 2\n"

    # Hit it again, to check that it doesn't keep applying
    wait_for_done = await move_to_next_breakpoint(client, session_id)
    assert wait_for_done["state"] == "stopped"
    assert wait_for_done["current_position"] is None

    assert Path(std_out_path).read_text() == (
        "it started\nloop number 0\nloop number 1\nloop number 2\nloop number 3\nloop number 4\nit finished\n"
    )


async def test_set_breakpoint__update_condition(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN_WITH_LOOP)
    session_id = start_response["id"]
    std_out_path = start_response["std_out_path"]

    bp = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_LOOP, "line": 5},
    )

    expected_breakpoint = {
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_loop.py",
        "line": 5,
        "line_text": '        print(f"loop number {i}", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
    }

    assert bp.structured_content == expected_breakpoint

    wait_for_pause_1 = await move_to_next_breakpoint(client, session_id)
    expected_breakpoint["hit_count"] += 1
    assert wait_for_pause_1["current_position"] == expected_breakpoint

    # Check that no condition was used
    variables = await client.call_tool("list_variables", {"session_id": session_id})
    assert variables.structured_content == {
        "variables": [{"name": "i", "type": "int", "evaluate_name": "i", "value": "0", "children": None}],
    }
    assert Path(std_out_path).read_text() == "it started\n"

    # Update that breakpoint to have a condition
    bp = await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_LOOP, "line": 5, "condition": "i > 2"},
    )
    expected_breakpoint["hit_count"] = 0  # new breakpoint, hasn't been hit yet
    expected_breakpoint["condition"] = "i > 2"
    assert bp.structured_content == expected_breakpoint

    # Hit it again, to check that the newly added condition applies
    wait_for_pause_2 = await move_to_next_breakpoint(client, session_id)
    expected_breakpoint["hit_count"] += 1
    assert wait_for_pause_2["current_position"] == expected_breakpoint
    assert Path(std_out_path).read_text() == "it started\nloop number 0\nloop number 1\nloop number 2\n"
