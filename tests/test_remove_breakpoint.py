from fastmcp import Client

from tests.constants import FAKE_MAIN, PROJECT_ROOT
from tests.utils import create_session


async def test_remove_breakpoint(client: Client) -> None:
    """After setting two breakpoints, removing one leaves only the other."""
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    # Set two breakpoints on different lines
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13},
    )

    breakpoint_1 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
        "line": 7,
        "line_text": '    print("it started", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
    }
    breakpoint_2 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
        "line": 13,
        "line_text": '    print("it finished", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
    }

    # Remove a breakpoint that doesn't exist, see that nothing happens
    await client.call_tool(
        "remove_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 99},
    )

    # Verify both are present, despite the removal
    list_before = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert list_before.structured_content == {"breakpoints": [breakpoint_1, breakpoint_2], "breakpoints_muted": False}

    # Remove one breakpoint
    await client.call_tool(
        "remove_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )

    # Verify only the remaining breakpoint is listed
    list_after = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert list_after.structured_content == {"breakpoints": [breakpoint_2], "breakpoints_muted": False}
