from fastmcp import Client
import psutil

from tests.constants import FAKE_MAIN, FAKE_MAIN_MULTI_THREAD, PROJECT_ROOT
from tests.utils import MatchAny, create_session, eventual_assert, move_to_next_breakpoint


async def test_resume_and_pause(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN_MULTI_THREAD))["id"]

    first_resume = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "resume"},
    )
    assert first_resume.structured_content["state"] == "running"
    assert first_resume.structured_content["current_position"] is None

    # threads take some time to start up, so poll every 0.1 seconds for up to 3 seconds until they're all good
    async def all_threads_running() -> bool:
        threads = await client.call_tool("list_threads", {"session_id": session_id})
        return threads.structured_content == {
            "threads": [
                {"id": 1, "is_current": MatchAny(bool), "name": "MainThread", "state": "running"},
                {"id": 2, "is_current": MatchAny(bool), "name": "BusyWorker", "state": "running"},
                {"id": 4, "is_current": MatchAny(bool), "name": "DaemonOne", "state": "running"},
                {"id": 5, "is_current": MatchAny(bool), "name": "DaemonTwo", "state": "running"},
            ],
            "total_count": 4,
        }

    await eventual_assert(
        all_threads_running, otherwise="Threads did not reach expected running state within 3 seconds",
    )

    first_pause = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "pause"},
    )
    assert first_pause.structured_content["state"] == "paused"

    # threads also take some time to pause
    async def all_threads_paused() -> bool:
        threads = await client.call_tool("list_threads", {"session_id": session_id})
        return threads.structured_content == {
            "threads": [
                {"id": 1, "is_current": MatchAny(bool), "name": "MainThread", "state": "paused"},
                {"id": 2, "is_current": MatchAny(bool), "name": "BusyWorker", "state": "paused"},
                {"id": 4, "is_current": MatchAny(bool), "name": "DaemonOne", "state": "paused"},
                {"id": 5, "is_current": MatchAny(bool), "name": "DaemonTwo", "state": "paused"},
            ],
            "total_count": 4,
        }

    await eventual_assert(
        all_threads_paused, otherwise="Threads did not reach expected paused state within 3 seconds",
    )

    # our second resume works differently than the first, test that code path too.
    second_resume = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "resume"},
    )
    assert second_resume.structured_content["state"] == "running"

    await eventual_assert(
        all_threads_running, otherwise="Threads did not reach expected running state within 3 seconds",
    )


async def test_wait_for_pause(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )

    # check that the breakpoint was set, by hitting it.
    await client.call_tool("control_session", {"session_id": session_id, "action": "resume"})
    wait_for_pause_1 = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "wait_for_pause"},
    )
    assert wait_for_pause_1.structured_content == {
        "id": session_id,
        "debugee_pid": MatchAny(int),
        "breakpoints_muted": False,
        "state": "paused",
        "std_err_path": MatchAny(str),
        "std_out_path": MatchAny(str),
        "current_position": {
            "type": "line",
            "file": f"{PROJECT_ROOT}/tests/fakes/fake_main.py",
            "line": 7,
            "line_text": '    print("it started", flush=True)\n',
            "condition": None,
            "temporary": False,
            "hit_count": 0,
            "suspend_policy": "all",
        },
    }

    # check that wait_for_pause works even after we've chronologically hit the next breakpoint
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13},
    )
    await client.call_tool("control_session", {"session_id": session_id, "action": "resume"})

    expected_status = {
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
            "line_text": '    print("it finished", flush=True)\n',
            "condition": None,
            "temporary": False,
            "hit_count": 0,
            "suspend_policy": "all",
        },
    }

    # Wait for the breakpoint to get hit naturally
    async def naturally_paused() -> bool:
        updated_session = await client.call_tool("get_debugger_session", {"session_id": session_id})
        return updated_session.structured_content == expected_status

    await eventual_assert(naturally_paused, otherwise="Main thread did not pause naturally.")

    # check that waiting for pause at that naturally hit breakpoint doesn't advance us past it
    wait_for_pause_2 = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "wait_for_pause"},
    )
    assert wait_for_pause_2.structured_content == expected_status


async def test_stop__paused_session(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    await client.call_tool("set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 13})

    wait_for_pause = await move_to_next_breakpoint(client, session_id)
    assert wait_for_pause["state"] == "paused"
    assert wait_for_pause["current_position"]["line"] == 13

    # Capture the PID before stopping.
    debugee_pid = wait_for_pause["debugee_pid"]

    # Stop the session.
    stop_result = await client.call_tool("control_session", {"session_id": session_id, "action": "stop"})

    # Verify the session reports stopped state.
    assert stop_result.structured_content == {
        "id": session_id,
        "debugee_pid": debugee_pid,
        "state": "stopped",
        "current_position": None,
        "breakpoints_muted": False,
        "std_out_path": MatchAny(str),
        "std_err_path": MatchAny(str),
    }

    # Verify the process has exited.
    async def process_exited() -> bool:
        return psutil.Process(debugee_pid).status() == psutil.STATUS_ZOMBIE

    await eventual_assert(process_exited, otherwise="Process did not exit within 3 seconds.")


async def test_stop__unstarted_session(client: Client) -> None:
    session = await create_session(client, file_path=FAKE_MAIN)
    session_id = session["id"]
    debugee_pid = session["debugee_pid"]

    stop_result = await client.call_tool("control_session", {"session_id": session_id, "action": "stop"})
    assert stop_result.structured_content == {
        "id": session_id,
        "debugee_pid": debugee_pid,
        "state": "stopped",
        "current_position": None,
        "breakpoints_muted": False,
        "std_out_path": MatchAny(str),
        "std_err_path": MatchAny(str),
    }

    async def process_exited() -> bool:
        return psutil.Process(debugee_pid).status() == psutil.STATUS_ZOMBIE

    await eventual_assert(process_exited, otherwise="Process did not exit within 3 seconds.")


async def test_stop__running_process(client: Client) -> None:
    session = await create_session(client, file_path=FAKE_MAIN_MULTI_THREAD)
    session_id = session["id"]
    debugee_pid = session["debugee_pid"]

    # get the process into a known running state
    await client.call_tool("control_session", {"session_id": session_id, "action": "resume"})

    async def all_threads_running() -> bool:
        threads = await client.call_tool("list_threads", {"session_id": session_id})
        return threads.structured_content == {
            "threads": [
                {"id": 1, "is_current": MatchAny(bool), "name": "MainThread", "state": "running"},
                {"id": 2, "is_current": MatchAny(bool), "name": "BusyWorker", "state": "running"},
                {"id": 4, "is_current": MatchAny(bool), "name": "DaemonOne", "state": "running"},
                {"id": 5, "is_current": MatchAny(bool), "name": "DaemonTwo", "state": "running"},
            ],
            "total_count": 4,
        }

    await eventual_assert(
        all_threads_running, otherwise="Threads did not reach expected running state within 3 seconds",
    )

    stop_result = await client.call_tool("control_session", {"session_id": session_id, "action": "stop"})
    assert stop_result.structured_content == {
        "id": session_id,
        "debugee_pid": debugee_pid,
        "state": "stopped",
        "current_position": None,
        "breakpoints_muted": False,
        "std_out_path": MatchAny(str),
        "std_err_path": MatchAny(str),
    }

    async def process_exited() -> bool:
        return psutil.Process(debugee_pid).status() == psutil.STATUS_ZOMBIE

    await eventual_assert(process_exited, otherwise="Process did not exit within 3 seconds.")
