from typing import Annotated
import uuid

from annotations import ProjectPath
from constants import TEMP_DIR
from db import get_db
from db_models import DBSession
from enums import DebuggerState
from frontend_models import StartDebuggerSessionResponse


def start_debugger_session(
    projectPath: ProjectPath,
    pythonPath: Annotated[str, "Absolute path to the Python executable to use when running the program."],
    filePath: Annotated[str, "File path of the Python program to debug, relative to the project root."],
    timeout: Annotated[int, "Timeout in milliseconds to wait for the debug session to start. Default: 60000."] = 60000,
    programArguments: Annotated[str | None, "Optional command-line arguments given to the program."] = None,
    workingDirectory: Annotated[
        str | None,
        "Optional working directory override for this program. Missing/null or empty string defaults to `projectPath`.",
    ] = None,
    envs: Annotated[
        dict[str, str] | None,
        "Optional environment variables to set during the program's execution. "
        "Missing/null keeps existing env unchanged; when provided, values are merged over existing env.",
    ] = None,
) -> StartDebuggerSessionResponse:
    """Start a debugger session for a given Python program in the current project.
Use this tool to start a debugger session.
The session will be started and you can then use other debugger tools to control execution.
This MCP server will wait for session creation to succeed, up to `timeout` milliseconds.
The program will be started in a paused state, so you can set breakpoints that you expect to be hit during startup.

Next call:
- `get_stack` and `get_frame_values` (or `evaluate_expression`) for runtime evidence.

Returns a flat result with debugger session metadata."""

    if envs is None:
        envs = {}

    with get_db(projectPath):
        session_id = str(uuid.uuid4())
        full_output_path = str(TEMP_DIR / f"{session_id}.output")

        # TODO: actually do iiiiit
        # subprocess.Popen()

        session = DBSession.create(id=session_id, state=DebuggerState.PAUSED.value)
        return StartDebuggerSessionResponse(
            sessionId=session.id,
            state=session.state,
            breakpointsMuted=session.breakpoints_muted,
            fullOutputPath=full_output_path,
        )
