import os
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from constants import TEMP_DIR
from tests.constants import FAKE_MAIN, PROJECT_ROOT
from tests.fakes import fake_main
from tests.utils import MatchAny, create_session, move_to_next_breakpoint


async def test_list_debugger_sessions__invalid(client: Client) -> None:
    with pytest.raises(ToolError, match=r"project_path must be an absolute directory path\."):
        await client.call_tool("list_debugger_sessions", {"project_path": "a/b/c"})


async def test_list_real_sessions(client: Client, clear_sessions: None) -> None:
    """Create 2 real sessions, check that they show up under the appropriate project path, but not under a different path."""
    session_id_0 = (await create_session(client, file_path=FAKE_MAIN))["id"]
    session_id_1 = (await create_session(client, file_path=FAKE_MAIN))["id"]

    result_1 = await client.call_tool("list_debugger_sessions", {"project_path": str(PROJECT_ROOT)})
    assert result_1.structured_content == {
        "sessions": [
            {
                "breakpoints_muted": False,
                "current_position": None,
                "debugee_pid": MatchAny(int),
                "id": session_id_0,
                "state": "paused",
                "std_out_path": f"{TEMP_DIR}{os.sep}{session_id_0}.stdout.txt",
                "std_err_path": f"{TEMP_DIR}{os.sep}{session_id_0}.stderr.txt",
            },
            {
                "breakpoints_muted": False,
                "current_position": None,
                "debugee_pid": MatchAny(int),
                "id": session_id_1,
                "state": "paused",
                "std_out_path": f"{TEMP_DIR}{os.sep}{session_id_1}.stdout.txt",
                "std_err_path": f"{TEMP_DIR}{os.sep}{session_id_1}.stderr.txt",
            },
        ],
    }
    sessions = result_1.structured_content["sessions"]
    assert sessions[0]["debugee_pid"] != sessions[1]["debugee_pid"]

    # set a breakpoint in one of the sessions, to see that `current_position` is populated
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id_0, "file_path": FAKE_MAIN, "line": 13},
    )
    # hit that breakpoint
    await move_to_next_breakpoint(client, session_id_0)

    result_2 = await client.call_tool("list_debugger_sessions", {"project_path": str(PROJECT_ROOT)})
    assert result_2.structured_content == {
        "sessions": [
            {
                "breakpoints_muted": False,
                "current_position": {
                    "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
                    "line": 13,
                    "line_text": '    print("it finished", flush=True)\n',
                    "hit_count": 1,
                    "temporary": False,
                },
                "debugee_pid": MatchAny(int),
                "id": session_id_0,
                "state": "paused",
                "std_out_path": f"{TEMP_DIR}{os.sep}{session_id_0}.stdout.txt",
                "std_err_path": f"{TEMP_DIR}{os.sep}{session_id_0}.stderr.txt",
            },
            {
                "breakpoints_muted": False,
                "current_position": None,
                "debugee_pid": MatchAny(int),
                "id": session_id_1,
                "state": "paused",
                "std_out_path": f"{TEMP_DIR}{os.sep}{session_id_1}.stdout.txt",
                "std_err_path": f"{TEMP_DIR}{os.sep}{session_id_1}.stderr.txt",
            },
        ],
    }


async def test_list_across_project_paths(client: Client, clear_sessions: None) -> None:
    """Test that two different sessions under two differnt project paths, both show up when listing sessions with no project path."""
    fake_main_abs_path = Path(fake_main.__file__).resolve()
    other_path = str(Path(__file__).parent.resolve())
    session_1 = await client.call_tool(
        "launch_debugger_session", {
            "project_path": other_path, "python_path": sys.executable, "file_path": fake_main_abs_path,
        },
    )
    session_2 = await client.call_tool(
        "launch_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": fake_main_abs_path,
        },
    )
    all_sessions = await client.call_tool("list_debugger_sessions")
    assert all_sessions.structured_content == {"sessions": [session_1.structured_content, session_2.structured_content]}

    # While we're in here, test that we aren't doing all-or-nothing filtering
    some_sessions = await client.call_tool("list_debugger_sessions", {"project_path": other_path})
    assert some_sessions.structured_content == {"sessions": [session_1.structured_content]}


async def test_project_path_dealiasing(client: Client, clear_sessions: None) -> None:
    """Test that we dealias /a/b/c and file:///a/b/c for project path lookup."""
    session = await client.call_tool(
        "launch_debugger_session",
        {"project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": FAKE_MAIN},
    )

    result = await client.call_tool("list_debugger_sessions", {"project_path": "file://" + str(PROJECT_ROOT)})
    assert result.structured_content == {"sessions": [session.structured_content]}
