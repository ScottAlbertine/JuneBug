from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN, FAKE_MAIN_MULTI_THREAD, FAKE_MAIN_WITH_IMPORT, PROJECT_ROOT
from tests.utils import MatchAny, create_session, eventual_assert, move_to_next_breakpoint


async def test_get_stack__invalid(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )

    await move_to_next_breakpoint(client, session_id)

    with pytest.raises(ToolError, match=r"Error calling tool 'get_stack': Thread 999 was not found."):
        await client.call_tool("get_stack", {"session_id": session_id, "thread_id": 999})

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool("get_stack", {"session_id": session_id, "timeout": -1})

    with pytest.raises(ToolError, match=r"limit\n.+Input should be greater than or equal to 1"):
        await client.call_tool("get_stack", {"session_id": session_id, "limit": 0})

    with pytest.raises(ToolError, match=r"offset\n.+Input should be greater than or equal to 0"):
        await client.call_tool("get_stack", {"session_id": session_id, "offset": -1})


async def test_basic(client: Client) -> None:
    """Test basic stack retrieval: create session, pause at breakpoint, get stack frames."""
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    # Set a breakpoint inside the main function
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7},
    )

    # Resume and wait for pause at the breakpoint
    await move_to_next_breakpoint(client, session_id)

    # Get the stack
    stack = await client.call_tool("get_stack", {"session_id": session_id})
    assert stack.structured_content == {
        "frames": [
            {
                "id": MatchAny(int),
                "name": "main",
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main.py"),
                "line": 7,
                "library_code": False,
            },
            {
                "id": MatchAny(int),
                "name": "<module>",
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main.py"),
                "line": 17,
                "library_code": False,
            },
            # these bottom two stack frames are interpreter dependant, let them be whatever they are
            # but check that they're labeled as library code
            {
                "id": MatchAny(int),
                "name": MatchAny(str),
                "file": MatchAny(str),
                "line": MatchAny(int),
                "library_code": True,
            },
            {
                "id": MatchAny(int),
                "name": MatchAny(str),
                "file": MatchAny(str),
                "line": MatchAny(int),
                "library_code": True,
            },
        ],
        "thread_id": 1,
        "total_frames": 4,
    }


async def test_deeper_stack_with_import(client: Client) -> None:
    """Test stack retrieval with a deeper call stack (across module imports)."""
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_IMPORT))["id"]

    # Set a breakpoint inside the add() function in fake_library (line 2: return a + b)
    await client.call_tool(
        "set_breakpoint",
        {"session_id": session_id, "file_path": str(Path("tests") / "fakes" / "fake_library.py"), "line": 2},
    )

    # Resume and wait for pause at the breakpoint
    await move_to_next_breakpoint(client, session_id)

    # Get the stack
    stack = await client.call_tool("get_stack", {"session_id": session_id})
    expected_frame_1 = {
        "id": MatchAny(int),
        "name": "add",
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_library.py"),
        "line": 2,
        "library_code": False,
    }
    expected_frame_2 = {
        "id": MatchAny(int),
        "name": "main",
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_import.py"),
        "line": 12,
        "library_code": False,
    }
    expected_frame_3 = {
        "id": MatchAny(int),
        "name": "<module>",
        "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_with_import.py"),
        "line": 17,
        "library_code": False,
    }
    assert stack.structured_content == {
        # the bottom two stack frames are interpreter dependant, let them be whatever they are
        "frames": [expected_frame_1, expected_frame_2, expected_frame_3, MatchAny(dict), MatchAny(dict)],
        "thread_id": 1,
        "total_frames": 5,
    }

    # while we're in here, check pagination, it's the exact same setup as above
    page_1 = await client.call_tool("get_stack", {"session_id": session_id, "limit": 2, "offset": 1})
    assert page_1.structured_content == {
        "frames": [expected_frame_2, expected_frame_3], "thread_id": 1, "total_frames": 5,
    }


async def test_specific_thread_id(client: Client) -> None:
    """Test getting stack for a specific thread in a multi-threaded session."""
    session_id = (await create_session(client, file_path=FAKE_MAIN_MULTI_THREAD))["id"]

    # Set a breakpoint in the BusyWorker thread
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_MULTI_THREAD, "line": 14},
    )

    # Hit that breakpoint
    await move_to_next_breakpoint(client, session_id)

    # Find the BusyWorker thread ID
    thread_id: int | None = None
    threads = await client.call_tool("list_threads", {"session_id": session_id})
    for thread in threads.structured_content["threads"]:
        if thread["name"] == "BusyWorker":
            thread_id = thread["id"]
    assert thread_id is not None, "BusyWorker thread not found."

    # Get stack for the BusyWorker thread, by thread ID
    # Only get the top frame, since that's the only one we care about
    stack = await client.call_tool("get_stack", {"session_id": session_id, "thread_id": thread_id, "limit": 1})
    assert stack.structured_content == {
        "frames": [
            {
                "id": MatchAny(int),
                "name": "worker_busy",
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
                "line": 14,
                "library_code": False,
            },
        ],
        "thread_id": thread_id,
        "total_frames": 4,
    }


async def test_get_stack_while_running(client: Client) -> None:
    """Test that you can, in fact, get a stack trace while running, not paused, and not at a breakpoint."""
    session_id = (await create_session(client, file_path=FAKE_MAIN_MULTI_THREAD))["id"]

    # The session starts in paused state. Resume it.
    resume = await client.call_tool("control_debugger_session", {"session_id": session_id, "action": "resume"})
    assert resume.structured_content["state"] == "running"

    # threads take some time to start up, so poll every 0.1 seconds for up to 3 seconds until they're all good
    async def all_threads_running() -> bool:
        threads = await client.call_tool("list_threads", {"session_id": session_id})
        return threads.structured_content == {
            "threads": [
                {"id": MatchAny(int), "is_current": MatchAny(bool), "name": "MainThread", "state": "running"},
                {"id": MatchAny(int), "is_current": MatchAny(bool), "name": "BusyWorker", "state": "running"},
                {"id": MatchAny(int), "is_current": MatchAny(bool), "name": "DaemonOne", "state": "running"},
                {"id": MatchAny(int), "is_current": MatchAny(bool), "name": "DaemonTwo", "state": "running"},
            ],
            "total_count": 4,
        }

    await eventual_assert(
        all_threads_running, otherwise="Threads did not reach expected running state within 3 seconds",
    )

    # the thread IDs change after several get_stack calls, refresh them before each call.
    threads = await client.call_tool("list_threads", {"session_id": session_id})
    thread_ids = {thread["name"]: thread["id"] for thread in threads.structured_content["threads"]}
    # While we're in here, test that timeouts work, since this is a 600ms operation
    with pytest.raises(ToolError, match=r"timed out"):
        await client.call_tool(
            "get_stack", {"session_id": session_id, "thread_id": thread_ids["MainThread"], "limit": 2, "timeout": 100},
        )

    threads = await client.call_tool("list_threads", {"session_id": session_id})
    thread_ids = {thread["name"]: thread["id"] for thread in threads.structured_content["threads"]}
    stack = await client.call_tool(
        "get_stack", {"session_id": session_id, "thread_id": thread_ids["MainThread"], "limit": 2},
    )
    assert stack.structured_content == {
        "frames": [
            {
                "id": MatchAny(int),
                "name": "main",
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
                "line": 38,
                "library_code": False,
            },
            {
                "id": MatchAny(int),
                "name": "<module>",
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
                "line": 43,
                "library_code": False,
            },
        ],
        "thread_id": thread_ids["MainThread"],
        "total_frames": 4,
    }

    threads = await client.call_tool("list_threads", {"session_id": session_id})
    thread_ids = {thread["name"]: thread["id"] for thread in threads.structured_content["threads"]}
    stack = await client.call_tool(
        "get_stack", {"session_id": session_id, "thread_id": thread_ids["BusyWorker"], "limit": 1},
    )
    assert stack.structured_content == {
        "frames": [
            {
                "id": MatchAny(int),
                "name": "worker_busy",
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
                "line": 14,
                "library_code": False,
            },
        ],
        "thread_id": thread_ids["BusyWorker"],
        "total_frames": 4,
    }

    threads = await client.call_tool("list_threads", {"session_id": session_id})
    thread_ids = {thread["name"]: thread["id"] for thread in threads.structured_content["threads"]}
    stack = await client.call_tool(
        "get_stack", {"session_id": session_id, "thread_id": thread_ids["DaemonOne"], "limit": 1},
    )
    assert stack.structured_content == {
        "frames": [
            {
                "id": MatchAny(int),
                "name": "worker_daemon",
                "file": str(PROJECT_ROOT / "tests" / "fakes" / "fake_main_multi_thread.py"),
                "line": 21,
                "library_code": False,
            },
        ],
        "thread_id": thread_ids["DaemonOne"],
        "total_frames": 4,
    }
