from pathlib import Path
import sys
from time import sleep

from fastmcp import Client

from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
import tests.fakes.fake_main_multi_thread as fake_main_multi_thread
from tests.utils import MAIN_THREAD, MatchAny


async def test_resume_and_pause(client: Client) -> None:
    file_to_breakpoint = str(Path(fake_main_multi_thread.__file__).relative_to(PROJECT_ROOT))
    create_result = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )
    session_id = create_result.structured_content["id"]

    # check that, until you resume the process, there's only the one thread.
    starting_threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert starting_threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    first_resume = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "resume"},
    )
    assert first_resume.structured_content["state"] == "running"

    # resume only makes sense with sleep, tragically for my test times
    sleep(1)

    threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert threads.structured_content == {
        "threads": [
            {"id": 1, "is_current": True, "name": "MainThread", "state": "running"},
            {"id": 2, "is_current": False, "name": "BusyWorker", "state": "running"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "running"},
            {"id": 5, "is_current": False, "name": "DaemonTwo", "state": "running"},
        ],
        "total_count": 4,
    }

    first_pause = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "pause"},
    )
    assert first_pause.structured_content["state"] == "paused"

    # sadly, a flat pause also needs time to let all the threads pause and inform the session about it
    sleep(1)

    threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert threads.structured_content == {
        "threads": [
            {"id": 1, "is_current": MatchAny(bool), "name": "MainThread", "state": "paused"},
            {"id": 2, "is_current": MatchAny(bool), "name": "BusyWorker", "state": "paused"},
            {"id": 4, "is_current": MatchAny(bool), "name": "DaemonOne", "state": "paused"},
            {"id": 5, "is_current": MatchAny(bool), "name": "DaemonTwo", "state": "paused"},
        ],
        "total_count": 4,
    }

    second_resume = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "resume"},
    )
    assert second_resume.structured_content["state"] == "running"

    threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert threads.structured_content == {
        "threads": [
            {"id": 1, "is_current": MatchAny(bool), "name": "MainThread", "state": "running"},
            {"id": 2, "is_current": MatchAny(bool), "name": "BusyWorker", "state": "running"},
            {"id": 4, "is_current": MatchAny(bool), "name": "DaemonOne", "state": "running"},
            {"id": 5, "is_current": MatchAny(bool), "name": "DaemonTwo", "state": "running"},
        ],
        "total_count": 4,
    }


async def test_wait_for_pause(client: Client) -> None:
    file_to_breakpoint = str(Path(fake_main.__file__).relative_to(PROJECT_ROOT))

    session = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": file_to_breakpoint,
        },
    )
    session_id = session.structured_content["id"]

    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 13},
    )

    # check that the breakpoint was set, by hitting it.
    wait_for_pause = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "wait_for_pause"},
    )
    assert wait_for_pause.structured_content == {
        "id": session_id,
        "debugee_pid": MatchAny(int),
        "breakpoints_muted": False,
        "state": "paused",
        "std_err_path": MatchAny(str),
        "std_out_path": MatchAny(str),
        "current_position": {
            "type": "line",
            "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
            "line": 13,
            "line_text": None,
            "condition": None,
            "temporary": False,
            "hit_count": 0,
            "suspend_policy": "all",
        },
    }


