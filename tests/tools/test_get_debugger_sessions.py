import os
from pathlib import Path
import sys

from fastmcp import Client
import pytest

from constants import TEMP_DIR
from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import MatchAny


async def test_get_real_sessions(client: Client) -> None:
    """Create 2 real sessions, check that they show up under the appropriate project path, but not under a different path."""
    await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )
    await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )
    result = await client.call_tool("get_debugger_sessions", {"project_path": str(PROJECT_ROOT)})

    empty_result = await client.call_tool("get_debugger_sessions", {"project_path": "fake"})

    # pre-pull some data for validation, we trust anything in here
    sessions = result.structured_content["sessions"]
    session_id_0 = sessions[0]["id"]
    session_id_1 = sessions[1]["id"]

    assert result.structured_content == {
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
    assert sessions[0]["debugee_pid"] != sessions[1]["debugee_pid"]

    assert empty_result.structured_content == {"sessions": []}
