from typing import Annotated

from annotations import ProjectPath
from models import SessionStatus
import session_service


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
) -> SessionStatus:
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

    session = session_service.launch_session(
        project_path, python_path, file_path, timeout, program_arguments, working_directory, env,
    )
    return session.get_status()
