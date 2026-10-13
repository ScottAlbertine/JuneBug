from pathlib import Path
import sys

from fastmcp import Client

from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main


async def test_mute_breakpoints(client: Client) -> None:
    file_to_breakpoint = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))
    session = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )

    session_id = session.structured_content["id"]

    # create two breakpoints
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 7},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 13},
    )

    # mute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"]

    # wait until pause
    ended_session = await client.call_tool("control_session", {"session_id": session_id, "action": "wait_for_pause"})
    assert ended_session.structured_content["id"] == session_id
    assert ended_session.structured_content["state"] == "stopped"
    assert ended_session.structured_content["current_position"] is None
    assert ended_session.structured_content["breakpoints_muted"]


async def test_unmute_breakpoints(client: Client) -> None:
    file_to_breakpoint = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))
    session = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )

    session_id = session.structured_content["id"]

    # mute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"]

    # create two breakpoints
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 7},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 13},
    )

    # unmute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": False})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"] == False

    # wait until pause, see that the first breakpoint was hit
    updated_session = await client.call_tool("control_session", {"session_id": session_id, "action": "wait_for_pause"})
    assert updated_session.structured_content["id"] == session_id
    assert updated_session.structured_content["state"] == "paused"
    assert updated_session.structured_content["current_position"] == {
        "type": "line",
        "id": 3,
        "file": "/Users/scott/Repos/JuneBug/tests/fakes/fake_main.py",
        "line": 7,
        "line_text": None,
        "condition": None,
        "temporary": False,
        "hit_count": 0,
        "suspend_policy": "all",
    }
    assert updated_session.structured_content["breakpoints_muted"] == False
