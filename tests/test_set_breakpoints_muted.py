from fastmcp import Client

from tests.constants import FAKE_MAIN, PROJECT_ROOT
from tests.utils import MatchAny, create_session, move_to_next_breakpoint


async def test_mute_breakpoints(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    # create two breakpoints
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13},
    )

    # mute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"]

    # resume, wait until pause, see that the program ran to completion and the session ended despite the breakpoints
    assert await move_to_next_breakpoint(client, session_id) == {
        'id': session_id,
        'state': 'stopped',
        'debugee_pid': MatchAny(int),
        'std_out_path': MatchAny(str),
        'std_err_path': MatchAny(str),
        'breakpoints_muted': True,
        'current_position': None,
    }


async def test_unmute_breakpoints(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    # mute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"]

    # create two breakpoints
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13},
    )

    # unmute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": False})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"] == False

    # wait until pause, see that the first breakpoint was hit
    updated_session = await move_to_next_breakpoint(client, session_id)
    assert updated_session["id"] == session_id
    assert updated_session["state"] == "paused"
    assert updated_session["current_position"] == {
        "type": "line",
        "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
        "line": 7,
        "line_text": '    print("it started", flush=True)\n',
        "temporary": False,
        "hit_count": 0,
        "suspend_policy": "all",
    }
    assert updated_session["breakpoints_muted"] == False
