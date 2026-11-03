"""This is a special test that tests that every tool properly handles a stopped session."""
from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN
from tests.utils import create_session, move_to_next_breakpoint

STOPPED_MESSAGE = r"Session has stopped, no more tool calls can be made to its id\. Start a new session instead\."


async def test_stopped_session(client: Client) -> None:
    """
    This is a special test that tests that every single tool properly handles a stopped session.
    I could split this out per-tool, but the redundant setup would be very slow.
    """
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    stopped = await move_to_next_breakpoint(client, session_id)
    assert stopped["state"] == "stopped"

    # The following tools are the exception to the rule, they don't error when called on a stopped session

    stop = await client.call_tool("control_debugger_session", {"session_id": session_id, "action": "stop"})
    assert stop.structured_content == stopped

    retrieved_session = await client.call_tool("get_debugger_session", {"session_id": session_id})
    assert retrieved_session.structured_content == stopped

    # The rest of these tools all error when called on a stopped session

    for action in ["step_into", "step_over", "step_out", "resume", "pause", "wait_for_pause"]:
        with pytest.raises(ToolError, match=STOPPED_MESSAGE):
            await client.call_tool("control_debugger_session", {"session_id": session_id, "action": action})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("evaluate_expression", {"session_id": session_id, "expression": "args"})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("get_stack", {"session_id": session_id})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("list_breakpoints", {"session_id": session_id})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("list_threads", {"session_id": session_id})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("list_variables", {"session_id": session_id})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("remove_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7})

    with pytest.raises(ToolError, match=STOPPED_MESSAGE):
        await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})
