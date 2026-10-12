from pathlib import Path
import sys
from time import sleep

from fastmcp import Client

from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
import tests.fakes.fake_main_multi_thread as fake_main_multi_thread
from tests.utils import MAIN_THREAD


async def test_simple(client: Client) -> None:
    create_result = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )
    session_id = create_result.structured_content["id"]

    threads = await client.call_tool("get_threads", {"session_id": session_id})
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}


async def test_multi_threaded(client: Client) -> None:
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

    await client.call_tool(
        "control_session", {"session_id": session_id, "action": "RESUME"},
    )

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

    # while we're in here, test thread pagination
    # it's the literal exact same setup as this test, so there's no point in doing it all twice
    page_1 = await client.call_tool("get_threads", {"session_id": session_id, "limit": 2, "offset": 1})
    assert page_1.structured_content == {
        "threads": [
            {"id": 2, "is_current": False, "name": "BusyWorker", "state": "running"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "running"},
        ],
        "total_count": 4,
    }
