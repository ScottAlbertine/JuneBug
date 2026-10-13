from pathlib import Path
import sys

from fastmcp import Client

from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_library as fake_library
import tests.fakes.fake_main_with_import as fake_main_with_import

_FAKE_MAIN_PATH = str(Path(fake_main_with_import.__file__).relative_to(PROJECT_ROOT))
_FAKE_LIB_PATH = str(Path(fake_library.__file__).relative_to(PROJECT_ROOT))


# TODO: make this a util function, it's used all over the place
async def _create_session(client: Client) -> str:
    """Start a debugger session and return (session_id, file_to_breakpoint)."""
    session_start = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": _FAKE_MAIN_PATH,
        },
    )
    return session_start.structured_content["id"]


async def test_list_breakpoints(client: Client) -> None:
    """After setting breakpoints, list_breakpoints returns them sorted by file then line."""
    session_id = await _create_session(client)

    all_breakpoints = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert all_breakpoints.structured_content == {"breakpoints": [], "breakpoints_muted": False}

    # Set two breakpoints on different lines, in the wrong order on purpose to test sorting
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": _FAKE_MAIN_PATH, "line": 10},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": _FAKE_MAIN_PATH, "line": 7},
    )

    # set another breakpoint in a different file, doing it against alphabetical order to test file sorting
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": _FAKE_LIB_PATH, "line": 2},
    )

    breakpoint_1 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_library.py",
        "line": 2,
        "line_text": None,
        "condition": None,
        "temporary": False,
        "suspend_policy": "all",
        "hit_count": 0,
    }
    breakpoint_2 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_import.py",
        "line": 7,
        "line_text": None,
        "condition": None,
        "temporary": False,
        "suspend_policy": "all",
        "hit_count": 0,
    }
    breakpoint_3 = {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main_with_import.py",
        "line": 10,
        "line_text": None,
        "condition": None,
        "temporary": False,
        "suspend_policy": "all",
        "hit_count": 0,
    }
    all_breakpoints = await client.call_tool("list_breakpoints", {"session_id": session_id})
    assert all_breakpoints.structured_content == {
        "breakpoints": [breakpoint_1, breakpoint_2, breakpoint_3], "breakpoints_muted": False,
    }

    just_main_breakpoints = await client.call_tool(
        "list_breakpoints", {"session_id": session_id, "file_path": _FAKE_MAIN_PATH},
    )
    assert just_main_breakpoints.structured_content == {
        "breakpoints": [breakpoint_2, breakpoint_3], "breakpoints_muted": False,
    }

    just_lib_breakpoints = await client.call_tool(
        "list_breakpoints", {"session_id": session_id, "file_path": _FAKE_LIB_PATH},
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
