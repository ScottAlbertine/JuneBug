from pathlib import Path
import sys

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
    file_to_breakpoint = str(Path(fake_main_multi_thread.__file__).relative_to(PROJECT_ROOT))
    create_result = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": file_to_breakpoint,
        },
    )
    session_id = create_result.structured_content["id"]

    # check that, until you resume the process, there's only the one thread.
    starting_threads = await client.call_tool("get_threads", {"session_id": session_id})
    assert starting_threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    # wait until all the threads are spawned
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 38},
    )
    await client.call_tool("control_session", {"session_id": session_id, "action": "WAIT_FOR_PAUSE"})

    # unbreakpoint that breakpoint
    await client.call_tool(
        "remove_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 38},
    )

    # add a breakpoint in the BusyWorker thread
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": file_to_breakpoint, "line": 14},
    )
    # wait until it's hit
    await client.call_tool("control_session", {"session_id": session_id, "action": "WAIT_FOR_PAUSE"})

    # then we can check that a non-main thread is current, and that the main thread is not current.
    threads = await client.call_tool("get_threads", {"session_id": session_id})
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
    page_1 = await client.call_tool("get_threads", {"session_id": session_id, "limit": 2, "offset": 1})
    assert page_1.structured_content == {
        "threads": [
            {"id": 2, "is_current": True, "name": "BusyWorker", "state": "paused"},
            {"id": 4, "is_current": False, "name": "DaemonOne", "state": "paused"},
        ],
        "total_count": 4,
    }
