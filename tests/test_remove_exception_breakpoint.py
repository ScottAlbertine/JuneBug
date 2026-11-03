from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN_WITH_EXCEPTIONS
from tests.utils import create_session


async def test_remove_exception_breakpoint__invalid(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS))["id"]

    with pytest.raises(
        ToolError,
        match=r"mode\n.+Input should be 'raised', 'unhandled' or 'user_unhandled' \[type=enum, input_value='definitely_not_valid', input_type=str]\n",
    ):
        await client.call_tool(
            "remove_exception_breakpoint", {
                "session_id": session_id,
                "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
                "mode": "definitely_not_valid",
            },
        )

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool(
            "remove_exception_breakpoint", {
                "session_id": session_id,
                "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
                "mode": "raised",
                "timeout": -1,
            },
        )


async def test_remove_exception_breakpoint(client: Client) -> None:
    """After setting two exception breakpoints, removing one leaves only the other."""
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS))["id"]

    # Set two exception breakpoints on different exceptions
    bp_set_1 = await client.call_tool(
        "set_exception_breakpoint",
        {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
            "mode": "raised",
        },
    )
    bp_set_2 = await client.call_tool(
        "set_exception_breakpoint",
        {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeUnCaughtException",
            "mode": "raised",
        },
    )

    breakpoint_1 = bp_set_1.structured_content
    breakpoint_2 = bp_set_2.structured_content

    # Remove an exception breakpoint that doesn't exist, see that nothing happens
    await client.call_tool("remove_exception_breakpoint", {"session_id": session_id})

    # Verify both are present, despite the removal
    list_before = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert list_before.structured_content == {
        "breakpoints_muted": False, "breakpoints": [], "exception_breakpoints": [breakpoint_1, breakpoint_2],
    }

    # Remove one exception breakpoint
    await client.call_tool(
        "remove_exception_breakpoint",
        {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
            "mode": "raised",
        },
    )

    # Verify only the remaining exception breakpoint is listed
    list_after = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert list_after.structured_content == {
        "breakpoints_muted": False, "breakpoints": [], "exception_breakpoints": [breakpoint_2],
    }
