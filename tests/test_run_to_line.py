from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN, FAKE_MAIN_MULTI_THREAD, FAKE_MAIN_WITH_VARIABLES, PROJECT_ROOT
from tests.utils import create_session


async def test_run_to_line__invalid(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool(
            "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7, "timeout": -1},
        )


async def test_run_to_line(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_VARIABLES))["id"]

    # Set a regular breakpoint on line 29
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES, "line": 29},
    )

    # Set a temporary breakpoint on line 30
    await client.call_tool(
        "set_breakpoint",
        {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES, "line": 31, "temporary": True},
    )

    # Run to line 33. This should skip both breakpoints.
    run_to_line = await client.call_tool(
        "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES, "line": 33},
    )
    # Should be paused at line 33
    assert run_to_line.structured_content["state"] == "paused"
    assert run_to_line.structured_content["current_position"] == {
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_variables.py"),
        "line": 33,
        "line_text": "    some_tuple = (1, 2, 3)\n",
        "temporary": True,
        "hit_count": 1,
    }

    # Both breakpoints should still be present, and unhit
    expected_breakpoints = {
        "breakpoints": [
            {
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_variables.py"),
                "line": 29,
                "line_text": "    some_int = 123\n",
                "temporary": False,
                "hit_count": 0,
            },
            {
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_variables.py"),
                "line": 31,
                "line_text": "    some_bool = True\n",
                "temporary": True,
                "hit_count": 0,
            },
        ],
        "breakpoints_muted": False,
    }
    remaining_breakpoints = await client.call_tool(
        "list_breakpoints", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES},
    )
    assert remaining_breakpoints.structured_content == expected_breakpoints

    # run_to_line to a later line, see that the temporary breakpoint from the first run_to_line is cleaned up
    run_to_line = await client.call_tool(
        "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES, "line": 35},
    )
    # Should be paused at line 35
    assert run_to_line.structured_content["state"] == "paused"
    assert run_to_line.structured_content["current_position"] == {
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_variables.py"),
        "line": 35,
        "line_text": "    some_object = Car()\n",
        "temporary": True,
        "hit_count": 1,
    }
    remaining_breakpoints = await client.call_tool(
        "list_breakpoints", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES},
    )
    assert remaining_breakpoints.structured_content == expected_breakpoints


async def test_run_to_line__already_running(client: Client) -> None:
    """Test that you can run_to_line even when all your threads are already running."""
    session = await create_session(client, file_path=FAKE_MAIN_MULTI_THREAD)
    session_id = session["id"]
    std_out_path = session["std_out_path"]

    await client.call_tool("control_debugger_session", {"session_id": session_id, "action": "resume"})

    run_to_line = await client.call_tool(
        "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN_MULTI_THREAD, "line": 14},
    )
    assert run_to_line.structured_content["state"] == "paused"
    assert run_to_line.structured_content["current_position"] == {
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
        "line": 14,
        "line_text": "        sleep(1)\n",
        "temporary": True,
        "hit_count": 1,
    }

    # while we're in here, test that you can run_to_line again to hit the same breakpoint in a loop
    # to confirm this, pull the std_out from this session
    existing_text = Path(std_out_path).read_text()

    # then run again
    run_to_line = await client.call_tool(
        "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN_MULTI_THREAD, "line": 14},
    )
    assert run_to_line.structured_content["state"] == "paused"
    assert run_to_line.structured_content["current_position"] == {
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
        "line": 14,
        "line_text": "        sleep(1)\n",
        "temporary": True,
        "hit_count": 1,
    }

    # then check for at least one more line of the worker running
    new_text = Path(std_out_path).read_text()
    added_text = new_text.replace(existing_text, "")
    assert "busy work" in added_text


async def test_run_to_line__runs_to_end(client: Client) -> None:
    """Test that you if you run_to_line on a breakpoint that never gets hit, the program runs to completion."""

    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    run_to_line = await client.call_tool(
        "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 10},
    )
    assert run_to_line.structured_content["state"] == "stopped"
    assert run_to_line.structured_content["current_position"] == None


async def test_run_to_line__timeout(client: Client) -> None:
    """Test that run_to_line times out if you don't reach the line."""

    session_id = (await create_session(client, file_path=FAKE_MAIN, program_arguments=["--loop-forever"]))["id"]

    with pytest.raises(ToolError, match=r"timed out"):
        await client.call_tool(
            "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13, "timeout": 100},
        )


async def test_run_to_line__breakpoints_muted(client: Client) -> None:
    """Test what happens when you run_to_line with breakpoints muted, should be identical to the regular behavior."""
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})

    run_to_line = await client.call_tool(
        "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )
    assert run_to_line.structured_content["state"] == "paused"
    assert run_to_line.structured_content["current_position"] == {
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main.py"),
        "line": 7,
        "line_text": '    print("it started", flush=True)\n',
        "temporary": True,
        "hit_count": 1,
    }
