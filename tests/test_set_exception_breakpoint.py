from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from tests.constants import FAKE_MAIN_WITH_EXCEPTIONS, PROJECT_ROOT
from tests.utils import MatchAny, create_session, move_to_next_breakpoint


async def test_set_exception_breakpoint__invalid(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS))["id"]

    with pytest.raises(
        ToolError,
        match=r"mode\n.+Input should be 'raised', 'unhandled' or 'user_unhandled' \[type=enum, input_value='definitely_not_valid', input_type=str]\n",
    ):
        await client.call_tool(
            "set_exception_breakpoint", {
                "session_id": session_id,
                "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
                "mode": "definitely_not_valid",
            },
        )

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool(
            "set_exception_breakpoint", {
                "session_id": session_id,
                "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
                "mode": "raised",
                "timeout": -1,
            },
        )


async def test_set_exception_breakpoint__raised(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS)

    session_id = start_response["id"]
    pid = start_response["debugee_pid"]
    std_out_path = start_response["std_out_path"]

    breakpoint_response = await client.call_tool(
        "set_exception_breakpoint",
        {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException",
            "mode": "raised",
        },
    )
    assert breakpoint_response.structured_content == {
        "exception_type": "tests.fakes.fake_exceptions.SomeCaughtException", "mode": "raised",
    }

    assert await move_to_next_breakpoint(client, session_id) == {
        "id": session_id,
        "state": "paused",
        "debugee_pid": pid,
        "std_out_path": std_out_path,
        "std_err_path": MatchAny(str),
        "breakpoints_muted": False,
        "current_exception": {"type": "SomeCaughtException", "args": "('arg1', 'arg2')"},
        "current_position": {
            "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_exceptions.py"),
            "line": 9,
            "line_text": '        raise SomeCaughtException("arg1", "arg2")\n',
            "temporary": True,
            "hit_count": 1,
        },
    }

    assert Path(std_out_path).read_text() == "it got into the try\n"
    assert psutil.Process(pid).is_running()

    # Check that we null out current_exception upon resume
    after_resume = await client.call_tool("control_debugger_session", {"session_id": session_id, "action": "resume"})
    assert after_resume.structured_content == {
        "id": session_id,
        "state": "running",
        "debugee_pid": pid,
        "std_out_path": std_out_path,
        "std_err_path": MatchAny(str),
        "breakpoints_muted": False,
        "current_position": None,
    }


async def test_set_exception_breakpoint__uncaught(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS)

    session_id = start_response["id"]
    pid = start_response["debugee_pid"]
    std_out_path = start_response["std_out_path"]

    breakpoint_response = await client.call_tool(
        "set_exception_breakpoint",
        {
            "session_id": session_id,
            "exception_type": "tests.fakes.fake_exceptions.SomeUnCaughtException",
            # "mode": "unhandled",  # omit this, which tests that the default works
        },
    )
    assert breakpoint_response.structured_content == {
        "exception_type": "tests.fakes.fake_exceptions.SomeUnCaughtException", "mode": "unhandled",
    }

    assert await move_to_next_breakpoint(client, session_id) == {
        "id": session_id,
        "state": "paused",
        "debugee_pid": pid,
        "std_out_path": std_out_path,
        "std_err_path": MatchAny(str),
        "breakpoints_muted": False,
        "current_exception": {
            "type": "SomeUnCaughtException       (note: full exception trace is shown but execution is paused at: _run_module_as_main)",
            "args": "('arg1', 'arg2')",
        },
        "current_position": {
            "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_exceptions.py"),
            "line": 17,
            "line_text": '    raise SomeUnCaughtException("arg1", "arg2")\n',
            "temporary": True,
            "hit_count": 1,
        },
    }

    assert Path(std_out_path).read_text() == (
        "it got into the try\nit got into the except\nit got into the finally\nit left the try block\n"
    )
    assert psutil.Process(pid).is_running()


async def test_set_exception_breakpoint__user_unhandled(client: Client) -> None:
    start_response = await create_session(client, file_path=FAKE_MAIN_WITH_EXCEPTIONS)

    session_id = start_response["id"]
    pid = start_response["debugee_pid"]
    std_out_path = start_response["std_out_path"]

    # No exception_type, checks that we default to BaseException
    breakpoint_response = await client.call_tool(
        "set_exception_breakpoint", {"session_id": session_id, "mode": "user_unhandled"},
    )
    assert breakpoint_response.structured_content == {
        "exception_type": "BaseException", "mode": "user_unhandled",
    }

    assert await move_to_next_breakpoint(client, session_id) == {
        "id": session_id,
        "state": "paused",
        "debugee_pid": pid,
        "std_out_path": std_out_path,
        "std_err_path": MatchAny(str),
        "breakpoints_muted": False,
        "current_exception": {
            "type": "SomeUnCaughtException       (note: full exception trace is shown but execution is paused at: <module>)",
            "args": "('arg1', 'arg2')",
        },
        "current_position": {
            "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_exceptions.py"),
            "line": 17,
            "line_text": '    raise SomeUnCaughtException("arg1", "arg2")\n',
            "temporary": True,
            "hit_count": 1,
        },
    }

    assert Path(std_out_path).read_text() == (
        "it got into the try\nit got into the except\nit got into the finally\nit left the try block\n"
    )
    assert psutil.Process(pid).is_running()
