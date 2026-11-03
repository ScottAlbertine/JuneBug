from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN, FAKE_MAIN_WITH_EXCEPTIONS, PROJECT_ROOT
from tests.utils import MatchAny, create_session, move_to_next_breakpoint


async def test_set_breakpoints_muted__invalid(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool(
            "set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True, "timeout": -1},
        )


async def test_mute_breakpoints(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS))["id"]

    # create two breakpoints
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_EXCEPTIONS, "line": 8},
    )
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_EXCEPTIONS, "line": 11},
    )

    # and two really loud exception breakpoint
    await client.call_tool("set_exception_breakpoint", {"session_id": session_id, "mode": "raised"})
    await client.call_tool(
        "set_exception_breakpoint", {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
            "mode": "raised",
        },
    )

    # mute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"]

    # create a third breakpoint in the same file, to see that it doesn't take effect until unmute
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_EXCEPTIONS, "line": 13},
    )

    # and another exception breakpoint too
    await client.call_tool("set_exception_breakpoint", {"session_id": session_id, "mode": "unhandled"})

    # remove one of the original breakpoints, to see that removal doesn't reset breakpoints
    await client.call_tool(
        "remove_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_EXCEPTIONS, "line": 11},
    )

    # remove one of the original exception breakpoints, to see that removal doesn't reset breakpoints
    await client.call_tool(
        "remove_exception_breakpoint", {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
            "mode": "raised",
        },
    )

    # resume, wait until pause, see that the program ran to completion and the session ended despite the breakpoints
    assert await move_to_next_breakpoint(client, session_id) == {
        "id": session_id,
        "state": "stopped",
        "debugee_pid": MatchAny(int),
        "std_out_path": MatchAny(str),
        "std_err_path": MatchAny(str),
        "breakpoints_muted": True,
        "current_position": None,
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
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main.py"),
        "line": 7,
        "line_text": '    print("it started", flush=True)\n',
        "temporary": False,
        "hit_count": 1,
    }
    assert updated_session["breakpoints_muted"] == False


async def test_unmute_breakpoints__exception_breakpoint(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS))["id"]

    # mute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": True})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"]

    # create an exception breakpoint
    await client.call_tool(
        "set_exception_breakpoint",
        {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
            "mode": "raised",
        },
    )

    # unmute all breakpoints
    muted = await client.call_tool("set_breakpoints_muted", {"session_id": session_id, "breakpoints_muted": False})
    assert muted.structured_content["id"] == session_id
    assert muted.structured_content["breakpoints_muted"] == False

    # wait until pause, see that the exception breakpoint was hit
    updated_session = await move_to_next_breakpoint(client, session_id)
    assert updated_session["id"] == session_id
    assert updated_session["state"] == "paused"
    assert updated_session["current_exception"] == {"args": "('arg1', 'arg2')", "type": "SomeCaughtException"}
    assert updated_session["current_position"] == {
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_exceptions.py"),
        "line": 9,
        "line_text": '        raise SomeCaughtException("arg1", "arg2")\n',
        "temporary": True,
        "hit_count": 1,
    }
    assert updated_session["breakpoints_muted"] == False
