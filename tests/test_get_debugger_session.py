import os
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from constants import TEMP_DIR
from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import MatchAny


async def test_get_real_session(client: Client) -> None:
    file_to_breakpoint = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))
    session = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )
    session_id = session.structured_content["id"]

    result = await client.call_tool("get_debugger_session", {"session_id": session_id})
    assert result.structured_content == {
        "breakpoints_muted": False,
        "current_position": None,
        "debugee_pid": MatchAny(int),
        "id": session_id,
        "state": "paused",
        "std_out_path": f"{TEMP_DIR}{os.sep}{session_id}.stdout.txt",
        "std_err_path": f"{TEMP_DIR}{os.sep}{session_id}.stderr.txt",
    }

    with pytest.raises(
        ToolError,
        match=r"Error calling tool 'get_debugger_session': Session fake was not found\.",
    ):
        await client.call_tool("get_debugger_session", {"session_id": "fake"})
