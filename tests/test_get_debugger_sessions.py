import os
from pathlib import Path
import sys

from fastmcp import Client

from constants import TEMP_DIR
from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import MatchAny


async def test_get_real_sessions(client: Client, clear_sessions: None) -> None:
    """Create 2 real sessions, check that they show up under the appropriate project path, but not under a different path."""
    file_to_breakpoint = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))
    session_0 = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )
    session_1 = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )
    session_id_0 = session_0.structured_content["id"]
    session_id_1 = session_1.structured_content["id"]

    result_1 = await client.call_tool("get_debugger_sessions", {"project_path": str(PROJECT_ROOT)})
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
        "set_breakpoint", {"session_id": session_id_0, "file_path": file_to_breakpoint, "line": 13},
    )
    # hit that breakpoint
    await client.call_tool("control_session", {"session_id": session_id_0, "action": "wait_for_pause"})

    result_2 = await client.call_tool("get_debugger_sessions", {"project_path": str(PROJECT_ROOT)})
    assert result_2.structured_content == {
        "sessions": [
            {
                "breakpoints_muted": False,
                "current_position": {
                    "type": "line",
                    "file": "/Users/scott/Repos/JuneBug/tests/fakes/fake_main.py",
                    "line": 13,
                    "line_text": None,
                    "condition": None,
                    "hit_count": 0,
                    "temporary": False,
                    "suspend_policy": "all",
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

    empty_result = await client.call_tool("get_debugger_sessions", {"project_path": "fake"})
    assert empty_result.structured_content == {"sessions": []}
