import os

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from constants import TEMP_DIR
from tests.constants import FAKE_MAIN
from tests.utils import MatchAny, create_session


async def test_get_real_session(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

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
