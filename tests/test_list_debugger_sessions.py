import os

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from constants import TEMP_DIR
from tests.constants import FAKE_MAIN, PROJECT_ROOT
from tests.utils import MatchAny, create_session, move_to_next_breakpoint


async def test_list_debugger_sessions__invalid(client: Client) -> None:
    empty_result = await client.call_tool("list_debugger_sessions", {"project_path": "fake"})
    assert empty_result.structured_content == {"sessions": []}

    with pytest.raises(ToolError, match=r"project_path\n.+Missing required argument.+"):
        await client.call_tool("list_debugger_sessions")


async def test_get_real_sessions(client: Client, clear_sessions: None) -> None:
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
                    "type": "line",
                    "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
                    "line": 13,
                    "line_text": '    print("it finished", flush=True)\n',
                    "hit_count": 0,
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
