from pathlib import Path
from unittest.mock import patch

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

import session_service
from tests.constants import FAKE_MAIN, MAIN_THREAD
from tests.utils import create_session


async def test_automatic_single_session_finding(client: Client, clear_sessions: None) -> None:
    # create a session
    first_session = await create_session(client, file_path=FAKE_MAIN)

    # get its threads without a session ID
    threads = await client.call_tool("list_threads")
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    # stop the session
    await client.call_tool(
        "control_debugger_session", {"session_id": first_session["id"], "action": "stop"},
    )

    # create a second session
    await create_session(client, file_path=FAKE_MAIN)

    # see that you can get its threads without a session ID
    threads = await client.call_tool("list_threads")
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    # leave the second session running, and create a third session
    await create_session(client, file_path=FAKE_MAIN)

    # see that you need a session ID to distinguish between the two non-stopped sessions.
    with pytest.raises(
        ToolError,
        match=r"There is more than one active session, and you did not specify a session ID\. You must specify one\.",
    ):
        await client.call_tool("list_threads")


@patch("session_service.Session")  # don't make 100 real sessions for this, that is way too slow
def test_100_session_limit(clear_sessions: None) -> None:
    """Test that `session_service.attach_session` enforces a 100 session LRC limit."""
    first_session = session_service.attach_session("0", Path("/"), "", 0, 0)

    for i in range(1, 100):
        session_service.attach_session(str(i), Path("/"), "", 0, 0)
    assert len(session_service.SESSIONS) == 100

    first_session.stop.assert_not_called()

    # Check that the 101st session kicks out the first session
    session_service.attach_session("100", Path("/"), "", 0, 0)
    assert len(session_service.SESSIONS) == 100
    assert set(session_service.SESSIONS.keys()) == {str(i) for i in range(1, 101)}

    # Check that the session is stopped while being dropped
    first_session.stop.assert_called_once()
