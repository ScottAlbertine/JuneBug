from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN, MAIN_THREAD
from tests.utils import create_session


async def test_automatic_single_session_finding(client: Client, clear_sessions: None) -> None:
    # create a session
    await create_session(client, file_path=FAKE_MAIN)

    # get its threads without a session ID
    threads = await client.call_tool("list_threads")
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    # create a second session
    await create_session(client, file_path=FAKE_MAIN)

    # see that you need a session ID to distinguish between the two.
    with pytest.raises(
        ToolError,
        match=r"Error calling tool 'list_threads': Session ID is required for this tool call, and you did not specify a session ID\.",
    ):
        await client.call_tool("list_threads")
