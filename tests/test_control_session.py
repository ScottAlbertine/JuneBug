from pathlib import Path
import sys
from time import sleep

from fastmcp import Client

from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main_multi_thread as fake_main_multi_thread
from tests.utils import MAIN_THREAD


async def test_resume_and_pause(client: Client) -> None:
    create_result = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main_multi_thread.__file__).relative_to(PROJECT_ROOT)),
        },
    )
    session_id = create_result.structured_content["id"]

    # check that, until you resume the process, there's only the one thread.
    starting_threads = await client.call_tool("get_threads", {"session_id": session_id})
    assert starting_threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    first_resume = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "RESUME"},
    )
    assert first_resume.structured_content["state"] == "running"

    # TODO: replace this with setting a breakpoint before resuming the session, then resume, then wait until stopped, then check threads
    # that should reduce this wait time down to minimum
    sleep(1)

    threads = await client.call_tool("get_threads", {"session_id": session_id})
    assert threads.structured_content == {
        "threads": [
            {"id": 1, "is_current": False, "name": "MainThread", "state": "running"},
            {"id": 2, "is_current": False, "name": "BusyWorker", "state": "running"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "running"},
            {"id": 5, "is_current": False, "name": "DaemonTwo", "state": "running"},
        ],
        "total_count": 4,
    }

    first_pause = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "PAUSE"},
    )
    assert first_pause.structured_content["state"] == "paused"

    threads = await client.call_tool("get_threads", {"session_id": session_id})
    assert threads.structured_content == {
        "threads": [
            {"id": 1, "is_current": False, "name": "MainThread", "state": "paused"},
            {"id": 2, "is_current": False, "name": "BusyWorker", "state": "paused"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "paused"},
            {"id": 5, "is_current": False, "name": "DaemonTwo", "state": "paused"},
        ],
        "total_count": 4,
    }

    second_resume = await client.call_tool(
        "control_session", {"session_id": session_id, "action": "RESUME"},
    )
    assert first_resume.structured_content["state"] == "running"

    threads = await client.call_tool("get_threads", {"session_id": session_id})
    assert threads.structured_content == {
        "threads": [
            {"id": 1, "is_current": False, "name": "MainThread", "state": "running"},
            {"id": 2, "is_current": False, "name": "BusyWorker", "state": "running"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "running"},
            {"id": 5, "is_current": False, "name": "DaemonTwo", "state": "running"},
        ],
        "total_count": 4,
    }
