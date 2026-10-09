"""Shared test configuration and fixtures."""

from pathlib import Path
from typing import AsyncGenerator, Generator

from fastmcp import Client
import pytest
import pytest_asyncio

import db
from main import mcp
from tests.utils import kill_processes_by_module

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Module names whose running processes should be killed at session teardown.
# Add new test target modules here as they are created.
CLEANUP_MODULES = ["fake_main"]


@pytest.fixture(autouse=True, scope="function")
def clean_dbs() -> None:
    """To prevent tests affecting each other, always start each test with no databases."""
    db.databases = {}


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
