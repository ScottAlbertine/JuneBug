from fastmcp import Client

from tests.constants import FAKE_MAIN, FAKE_MAIN_MULTI_THREAD, MAIN_THREAD
from tests.utils import create_session, eventual_assert, move_to_next_breakpoint


async def test_simple(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}


async def test_multi_threaded(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN_MULTI_THREAD))["id"]

    # check that, until you resume the process, there's only the one thread.
    starting_threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert starting_threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    # wait until all the threads are spawned
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_MULTI_THREAD, "line": 38},
    )
    await move_to_next_breakpoint(client, session_id)

    # unbreakpoint that breakpoint
    await client.call_tool(
        "remove_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_MULTI_THREAD, "line": 38},
    )

    # add a breakpoint in the BusyWorker thread
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_MULTI_THREAD, "line": 14},
    )
    # wait until it's hit
    await move_to_next_breakpoint(client, session_id)

    # then we can check that a non-main thread is current, and that the main thread is not current.
    threads = await client.call_tool("list_threads", {"session_id": session_id})
    assert threads.structured_content == {
        "threads": [
            {"id": 1, "is_current": False, "name": "MainThread", "state": "paused"},
            {"id": 2, "is_current": True, "name": "BusyWorker", "state": "paused"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "paused"},
            {"id": 5, "is_current": False, "name": "DaemonTwo", "state": "paused"},
        ],
        "total_count": 4,
    }

    # while we're in here, test thread pagination
    # it's the literal exact same setup as this test, so there's no point in doing it all twice
    page_1 = await client.call_tool("list_threads", {"session_id": session_id, "limit": 2, "offset": 1})
    assert page_1.structured_content == {
        "threads": [
            {"id": 2, "is_current": True, "name": "BusyWorker", "state": "paused"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "paused"},
        ],
        "total_count": 4,
    }


async def test_running_threads(client: Client) -> None:
    """See that we correctly report running threads as running, and that we report the main thread as current on first resume."""
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
                {"id": 1, "is_current": True, "name": "MainThread", "state": "running"},
                {"id": 2, "is_current": False, "name": "BusyWorker", "state": "running"},
                {"id": 4, "is_current": False, "name": "DaemonOne", "state": "running"},
                {"id": 5, "is_current": False, "name": "DaemonTwo", "state": "running"},
            ],
            "total_count": 4,
        }

    await eventual_assert(
        all_threads_running, otherwise="Threads did not reach expected running state within 3 seconds",
    )
