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
            "projectPath": str(PROJECT_ROOT),
            "pythonPath": sys.executable,
            "filePath": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )
    await client.call_tool(
        "start_debugger_session", {
            "projectPath": str(PROJECT_ROOT),
            "pythonPath": sys.executable,
            "filePath": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )
    result = await client.call_tool("get_debugger_sessions", {"projectPath": str(PROJECT_ROOT)})

    empty_result = await client.call_tool("get_debugger_sessions", {"projectPath": "fake"})

    # pre-pull some data for validation, we trust anything in here
    sessions = result.structured_content["sessions"]
    session_id_0 = sessions[0]["id"]
    session_id_1 = sessions[1]["id"]

    assert result.structured_content == {
        "sessions": [
            {
                "breakpointsMuted": False,
                "currentPosition": None,
                "debugeePid": MatchAny(int),
                "id": session_id_0,
                "state": "paused",
                "stdOutPath": f"{TEMP_DIR}{os.sep}{session_id_0}.stdout.txt",
                "stdErrPath": f"{TEMP_DIR}{os.sep}{session_id_0}.stderr.txt",
            },
            {
                "breakpointsMuted": False,
                "currentPosition": None,
                "debugeePid": MatchAny(int),
                "id": session_id_1,
                "state": "paused",
                "stdOutPath": f"{TEMP_DIR}{os.sep}{session_id_1}.stdout.txt",
                "stdErrPath": f"{TEMP_DIR}{os.sep}{session_id_1}.stderr.txt",
            },
        ],
    }
    assert sessions[0]["debugeePid"] != sessions[1]["debugeePid"]

    assert empty_result.structured_content == {"sessions": []}
