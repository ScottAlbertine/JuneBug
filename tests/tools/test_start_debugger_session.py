import os
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from constants import TEMP_DIR
from tests.conftest import PROJECT_ROOT
import tests.fakes.fake_main as fake_main
from tests.utils import MatchAny, MatchRegex


async def test_simple(client: Client, clear_sessions: None) -> None:
    create_result = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
        },
    )
    get_result = await client.call_tool("get_debugger_sessions", {"project_path": str(PROJECT_ROOT)})

    session_id = create_result.structured_content["id"]
    expected_session = {
        "breakpoints_muted": False,
        "current_position": None,
        "debugee_pid": MatchAny(int),
        "id": session_id,
        "state": "paused",
        "std_out_path": f"{TEMP_DIR}{os.sep}{session_id}.stdout.txt",
        "std_err_path": f"{TEMP_DIR}{os.sep}{session_id}.stderr.txt",
    }

    assert create_result.structured_content == expected_session
    proc = psutil.Process(create_result.structured_content["debugee_pid"])
    assert proc.is_running()
    assert proc.cmdline() == [
        MatchRegex(r".+[Pp]ython3?"),  # don't worry about symlinks, just make sure it's python of some sort
        "-Xfrozen_modules=off",
        "-m", "debugpy",
        "--listen", MatchRegex(r"\d{4,5}"),
        "--wait-for-client",
        "tests/fakes/fake_main.py",
    ]
    assert proc.cwd() == str(PROJECT_ROOT)

    # Check that stdout and stderr have been created, but not written to.
    # This proves that the files were opened, and that fake_main hasn't actually started yet.
    assert Path(create_result.structured_content["std_out_path"]).read_text() == ""
    assert Path(create_result.structured_content["std_err_path"]).read_text() == ""

    # Check that the DB insert succeeded by using `get_debugger_sessions`
    assert get_result.structured_content == {"sessions": [expected_session]}


async def test_fancy(client: Client, clear_sessions: None) -> None:
    result = await client.call_tool(
        "start_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
            "program_arguments": ["a", "b", "c"],
            "working_directory": TEMP_DIR,
            "env": {"some": "body", "once": "told me"},
        },
    )

    proc = psutil.Process(result.structured_content["debugee_pid"])
    assert proc.is_running()
    assert proc.cmdline() == [
        MatchRegex(r".+[Pp]ython3?"),  # don't worry about symlinks, just make sure it's python of some sort
        "-Xfrozen_modules=off",
        "-m", "debugpy",
        "--listen", MatchRegex(r"\d{4,5}"),
        "--wait-for-client",
        "tests/fakes/fake_main.py",
        "a", "b", "c",
    ]
    assert proc.cwd().endswith(str(TEMP_DIR))  # more symlink weirdness
    env = proc.environ()
    assert env["some"] == "body"
    assert env["once"] == "told me"


async def test_bad_python_path(client: Client, clear_sessions: None) -> None:
    with pytest.raises(
        ToolError,
        match=r"Error calling tool 'start_debugger_session': \[Errno 2] No such file or directory: '/not/a/real/path'",
    ):
        await client.call_tool(
            "start_debugger_session", {
                "project_path": str(PROJECT_ROOT),
                "python_path": "/not/a/real/path",
                "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
            },
        )


async def test_debugpy_install_failure(client: Client, clear_sessions: None) -> None:
    with pytest.raises(
        ToolError,
        match=r"Failed to install debugpy with .+?\. \n\n Stderr: \n sample stderr \n\n Stdout: \n sample stdout \n",
    ):
        await client.call_tool(
            "start_debugger_session", {
                "project_path": str(PROJECT_ROOT),
                "python_path": str(Path(__file__).parent.parent / "fakes" / "python_that_cant_install_debugpy.sh"),
                "file_path": str(Path(fake_main.__file__).relative_to(PROJECT_ROOT)),
            },
        )
