from pathlib import Path
from typing import Annotated

from pydantic import Field

from annotations import ProjectPath
from exceptions import AbsolutePathError
from models import SessionStatus
import session_service
from utils import normalize_file_path, wait_for_timeout


async def launch_debugger_session(
    project_path: ProjectPath,
    python_path: Annotated[str, "Absolute path to the Python executable to use when running the program."],
    file_path: Annotated[str, "File path of the Python program to debug, relative to `project_path`."],
    timeout: Annotated[
        int, Field(description="Timeout in milliseconds to wait for the debug session to start. Default: 60000.", ge=0),
    ] = 60000,
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
    """
    Launch a new Python program under the debugger and create a debug session.

    This tool spawns a new Python process running through debugpy, which pauses on
    startup, before the first line has run, waiting for the debugger to connect.
    Once connected, the process remains paused and ready for breakpoints, stepping, and inspection.

    Preconditions:
    - The project_path must point to an existing project directory.
    - The python_path must point to a valid Python executable. debugpy will be
      installed for that Python if not already present.
    - The file_path must exist and be a Python file within or relative to the project.

    Behavior:
    - Installs debugpy for the target Python executable if needed.
    - Launches the target file via debugpy in --wait-for-client mode, so all threads start paused.
    - Connects to the debuggee, registering a new session with an auto-generated ID.
    - The debugee's stdout and stderr are captured to temp files (paths returned
      in the SessionStatus).
    - Blocks until the debugger connects or the timeout expires.

    Next call guidance:
    - Use the returned session_id for all subsequent debugger calls (breakpoints,
      stepping, variables). If you have only one active session, session_id can be
      omitted.
    - The session starts in a paused state. Set breakpoints with set_breakpoint,
      then call control_debugger_session with action "resume" to begin execution.
    - To check output, read the std_out_path or std_err_path from the returned status.
    """
    try:
        normal_project_path = normalize_file_path(project_path)
    except ValueError:
        raise AbsolutePathError("project_path")
    normal_file_path = normalize_file_path(file_path, project_path)
    normal_working_directory: Path | None = None
    if working_directory is not None:
        normal_working_directory = normalize_file_path(working_directory, project_path)
    # don't normalize python_path, since it might be just "python", which is neither an absolute nor a relative path

    async def go() -> SessionStatus:
        session = await session_service.launch_session(
            normal_project_path,
            python_path,
            normal_file_path,
            [] if program_arguments is None else program_arguments,
            normal_working_directory,
            {} if env is None else env,
        )
        return await session.get_status()

    return await wait_for_timeout(go(), timeout)
