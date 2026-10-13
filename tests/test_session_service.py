from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import MAIN_THREAD


async def test_automatic_single_session_finding(client: Client, clear_sessions: None) -> None:
    # create a session
    await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )

    # get its threads without a session ID
    threads = await client.call_tool("get_threads")
    assert threads.structured_content == {"threads": [MAIN_THREAD], "total_count": 1}

    # create a second session
    await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )

    # see that you need a session ID to distinguish between the two.
    with pytest.raises(
        ToolError,
        match=r"Error calling tool 'get_threads': Session ID is required for this tool call, and you did not specify a session ID\.",
    ):
        threads = await client.call_tool("get_threads")
