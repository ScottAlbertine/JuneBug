from fastmcp import Client

from tests.constants import FAKE_LIBRARY, FAKE_MAIN_WITH_IMPORT, PROJECT_ROOT
from tests.utils import create_session


async def test_list_breakpoints(client: Client) -> None:
    """After setting breakpoints, list_breakpoints returns them sorted by file then line."""
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_IMPORT))["id"]

    all_breakpoints = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert all_breakpoints.structured_content == {"breakpoints": [], "breakpoints_muted": False}

    # Set two breakpoints on different lines, in the wrong order on purpose to test sorting
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_IMPORT, "line": 13},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_IMPORT, "line": 8},
    )

    # set another breakpoint in a different file, doing it against alphabetical order to test file sorting
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_LIBRARY, "line": 2},
    )

    breakpoint_1 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_library.py",
        "line": 2,
        "line_text": "    return a + b\n",
        "temporary": False,
        "hit_count": 0,
    }
    breakpoint_2 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_import.py",
        "line": 8,
        "line_text": '    print("it started", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
    }
    breakpoint_3 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_import.py",
        "line": 13,
        "line_text": '    print("it finished", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
    }
    all_breakpoints = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert all_breakpoints.structured_content == {
        "breakpoints": [breakpoint_1, breakpoint_2, breakpoint_3], "breakpoints_muted": False,
    }

    just_main_breakpoints = await client.call_tool(
        "list_breakpoints", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_IMPORT},
    )
    assert just_main_breakpoints.structured_content == {
        "breakpoints": [breakpoint_2, breakpoint_3], "breakpoints_muted": False,
    }

    just_lib_breakpoints = await client.call_tool(
        "list_breakpoints", {"session_id": session_id, "file_path": FAKE_LIBRARY},
    )
    assert just_lib_breakpoints.structured_content == {"breakpoints": [breakpoint_1], "breakpoints_muted": False}

    nonexistent_file_breakpoints = await client.call_tool(
        "list_breakpoints", {"session_id": session_id, "file_path": "nonexistent.py"},
    )
    assert nonexistent_file_breakpoints.structured_content == {"breakpoints": [], "breakpoints_muted": False}

    # mute breakpoints, and check that they're still shown, but are shown as muted
    await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})

    muted_breakpoints = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert muted_breakpoints.structured_content == {
        "breakpoints": [breakpoint_1, breakpoint_2, breakpoint_3], "breakpoints_muted": True,
    }
