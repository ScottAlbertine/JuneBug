"""Shared test configuration and fixtures."""
from signal import SIGKILL
from typing import AsyncGenerator, Generator

from fastmcp import Client
from psutil import NoSuchProcess, Process
import pytest
import pytest_asyncio

from main import mcp
import session_service


def _kill_all_debugees() -> None:
    """Kill all debugee processes that we know about in SESSIONS."""
    for session in session_service.SESSIONS.values():
        if not isinstance(session.debugee_pid, int):  # we have some mocked sessions
            continue  # skip those, there's nothing to kill for them
        try:
            Process(session.debugee_pid).send_signal(SIGKILL)
        except NoSuchProcess:
            pass


@pytest.fixture()
def clear_sessions() -> None:
    """These tests list sessions, so they need to clear that list before each one runs."""
    _kill_all_debugees()
    session_service.SESSIONS.clear()


@pytest.fixture(autouse=True, scope="session")
def _cleanup_test_processes() -> Generator[None, None, None]:
    """Kill all debugee processes spawned by this worker at session teardown.

    With pytest-xdist, each worker is its own process with its own SESSIONS dict,
    so we only kill the processes we actually spawned (tracked by PID in sessions).
    """
    yield
    _kill_all_debugees()


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[Client, None]:
    """Provide an MCP client connected to the local server."""
    async with Client(mcp) as client:
        yield client
