import os
from pathlib import Path
import re
import sys

from fastmcp import Client
from fastmcp.exceptions import ToolError
import psutil
import pytest

from constants import TEMP_DIR
from tests.constants import FAKE_MAIN, PROJECT_ROOT
from tests.utils import MatchAny, MatchRegex


async def test_launch_debugger_session__invalid(client: Client) -> None:

    with pytest.raises(ToolError, match=r"project_path\n.+Missing required argument"):
        await client.call_tool("launch_debugger_session", {"python_path": sys.executable, "file_path": FAKE_MAIN})

    with pytest.raises(ToolError, match=r"project_path must be an absolute directory path\."):
        await client.call_tool(
            "launch_debugger_session", {"project_path": "a/b/c", "python_path": sys.executable, "file_path": FAKE_MAIN},
        )

    bad_dir = "C:\\not\\a\\real\\path" if os.name == "nt" else "/not/a/real/path"
    with pytest.raises(ToolError, match=re.escape(rf"Directory {bad_dir} was not found.")):
        await client.call_tool(
            "launch_debugger_session",
            {"project_path": bad_dir, "python_path": sys.executable, "file_path": FAKE_MAIN},
        )

    if os.name == "nt":
        expected_err = r"The system cannot find the file specified"
    else:
        expected_err = rf"No such file or directory: '{bad_dir}'"
    with pytest.raises(ToolError, match=expected_err):
        await client.call_tool(
            "launch_debugger_session", {
                "project_path": str(PROJECT_ROOT), "python_path": bad_dir, "file_path": FAKE_MAIN,
            },
        )

    with pytest.raises(ToolError, match=re.escape(rf"File {bad_dir} was not found.")):
        await client.call_tool(
            "launch_debugger_session", {
                "project_path": str(PROJECT_ROOT), "python_path": sys.executable, "file_path": bad_dir,
            },
        )

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool(
            "launch_debugger_session", {
                "project_path": str(PROJECT_ROOT),
                "python_path": sys.executable,
                "file_path": FAKE_MAIN,
                "timeout": -1,
            },
        )

    with pytest.raises(ToolError, match=re.escape(rf"Directory {bad_dir} was not found.")):
        await client.call_tool(
            "launch_debugger_session", {
                "project_path": str(PROJECT_ROOT),
                "python_path": sys.executable,
                "file_path": FAKE_MAIN,
                "working_directory": bad_dir,
            },
        )

    fake_python = "python_that_cant_install_debugpy.bat" if os.name == "nt" else "python_that_cant_install_debugpy.sh"
    with pytest.raises(
        ToolError,
        match=r"Failed to install debugpy with .+?\. \n\n Stderr: \n sample stderr \n\n Stdout: \n sample stdout \n",
    ):
        await client.call_tool(
            "launch_debugger_session", {
                "project_path": str(PROJECT_ROOT),
                "python_path": str(Path(__file__).parent / "fakes" / fake_python),
                "file_path": FAKE_MAIN,
            },
        )


async def test_simple(client: Client) -> None:
    create_result = await client.call_tool(
        "launch_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": FAKE_MAIN,
        },
    )

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
        str(PROJECT_ROOT / "tests" / "fakes" / "fake_main.py"),
    ]
    assert proc.cwd() == str(PROJECT_ROOT)

    # Check that stdout and stderr have been created, but not written to.
    # This proves that the files were opened, and that fake_main hasn't actually started yet.
    assert Path(create_result.structured_content["std_out_path"]).read_text() == ""
    assert Path(create_result.structured_content["std_err_path"]).read_text() == ""


async def test_fancy(client: Client) -> None:
    result = await client.call_tool(
        "launch_debugger_session", {
            "project_path": str(PROJECT_ROOT),
            "python_path": sys.executable,
            "file_path": FAKE_MAIN,
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
        str(PROJECT_ROOT / "tests" / "fakes" / "fake_main.py"),
        "a", "b", "c",
    ]
    assert os.path.samefile(Path(proc.cwd()), TEMP_DIR)  # more symlink weirdness
    env = proc.environ()
    if os.name == "nt":
        assert env["SOME"] == "body"
        assert env["ONCE"] == "told me"
    else:
        assert env["some"] == "body"
        assert env["once"] == "told me"
