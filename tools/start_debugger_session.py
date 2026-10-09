import subprocess
from typing import Annotated
import uuid

from annotations import ProjectPath
from constants import TEMP_DIR
from db import get_db
from db_models import DBDebugSession
from enums import DebuggerState
from frontend_models import DebugSession
from utils import find_free_port, install_debugpy


def start_debugger_session(
    project_path: ProjectPath,
    python_path: Annotated[str, "Absolute path to the Python executable to use when running the program."],
    file_path: Annotated[str, "File path of the Python program to debug, relative to the project root."],
    timeout: Annotated[int, "Timeout in milliseconds to wait for the debug session to start. Default: 60000."] = 60000,
    program_arguments: Annotated[list[str] | None, "Optional command-line arguments given to the program."] = None,
    working_directory: Annotated[
        str | None,
        "Optional working directory override for this program. Missing/null or empty string defaults to `project_path`.",
    ] = None,
    env: Annotated[
        dict[str, str] | None,
        "Optional environment variables to set during the program's execution. "
        "Missing/null keeps existing env unchanged; when provided, values are merged over existing env.",
    ] = None,
) -> DebugSession:
    """Start a debugger session for a given Python program in the current project.
Use this tool to start a debugger session.
The session will be started and you can then use other debugger tools to control execution.
This MCP server will wait for session creation to succeed, up to `timeout` milliseconds.
The program will be started in a paused state, so you can set breakpoints that you expect to be hit during startup.

Next call:
- `get_stack` and `get_frame_values` (or `evaluate_expression`) for runtime evidence.

Returns a flat result with debugger session metadata."""

    if program_arguments is None:
        program_arguments = []

    if env is None:
        env = {}

    install_debugpy(python_path)

    session_id = str(uuid.uuid4())
    stdout_file_path = TEMP_DIR / f"{session_id}.stdout.txt"
    stderr_file_path = TEMP_DIR / f"{session_id}.stderr.txt"
    port = find_free_port()
    debugee = subprocess.Popen(
        args=[
            python_path,
            "-Xfrozen_modules=off",
            "-m", "debugpy",
            "--listen", f"{port}",
            "--wait-for-client",
            file_path,
            *program_arguments,
        ],
        stdout=open(stdout_file_path, "w"),
        stderr=open(stderr_file_path, "w"),
        cwd=working_directory or project_path,
        env=env,
    )

    with get_db(project_path):
        session = DBDebugSession.create(
            id=session_id,
            pid=debugee.pid,
            port=port,
            # TODO: maybe a stdin path too?
            std_out_path=str(stdout_file_path),
            std_err_path=str(stderr_file_path),
            state=DebuggerState.PAUSED.value,
        )
        return DebugSession.from_db(session)
