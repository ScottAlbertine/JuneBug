"""Shared test configuration and fixtures."""

import pkgutil
from typing import AsyncGenerator, Generator

from fastmcp import Client
import pytest
import pytest_asyncio

from main import mcp
import session_service
from tests.utils import kill_processes_by_module

# Module names whose running processes should be killed at session teardown.
CLEANUP_MODULES = [
    name for _, name, _ in pkgutil.iter_modules(__import__("tests.fakes", fromlist=[""]).__path__)
]


@pytest.fixture()
def clear_sessions() -> None:
    """These tests list sessions, so they need to clear that list before each one runs."""
    session_service.SESSIONS.clear()


@pytest.fixture(autouse=True, scope="session")
def _cleanup_test_processes() -> Generator[None, None, None]:
    """Kill all test debugee processes at session teardown."""
    yield
    kill_processes_by_module(CLEANUP_MODULES)


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[Client, None]:
    """Provide an MCP client connected to the local server."""
    async with Client(mcp) as client:
        yield client
