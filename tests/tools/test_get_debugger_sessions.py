import os
from pathlib import Path
import sys

from fastmcp import Client
import pytest

from main import mcp
from tests.conftest import PROJECT_ROOT
import tests.fake_main as fake_main
from tests.utils import MatchAny, MatchRegex


@pytest.mark.asyncio
async def test_get_real_sessions() -> None:
    """Create 2 real sessions, check that they show up under the appropriate project path, but not under a different path."""
    async with Client(mcp) as client:
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

    structured_result = result.structured_content["result"]
    sessions = structured_result["sessions"]
    session_id_0 = sessions[0]["id"]
    session_id_1 = sessions[1]["id"]
    assert structured_result == {
        "sessions": [
            {
                "breakpointsMuted": False,
                "currentPosition": None,
                "debugeePid": MatchAny(int),
                "id": session_id_0,
                "state": "paused",
                "stdErrPath": MatchRegex(rf".+{os.sep}{session_id_0}\.stderr\.txt"),
                "stdOutPath": MatchRegex(rf".+{os.sep}{session_id_0}\.stdout\.txt"),
            },
            {
                "breakpointsMuted": False,
                "currentPosition": None,
                "debugeePid": MatchAny(int),
                "id": session_id_1,
                "state": "paused",
                "stdErrPath": MatchRegex(rf".+{os.sep}{session_id_1}\.stderr\.txt"),
                "stdOutPath": MatchRegex(rf".+{os.sep}{session_id_1}\.stdout\.txt"),
            },
        ],
    }
    assert sessions[0]["debugeePid"] != sessions[1]["debugeePid"]

    assert empty_result.structured_content["result"] == {"sessions": []}
