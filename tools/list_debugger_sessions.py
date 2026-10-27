from pathlib import Path
from typing import Annotated

from pydantic import Field

from exceptions import AbsolutePathError
from models import SessionStatuses
import session_service
from utils import normalize_file_path, wait_for_timeout


# This project path is optional, unlike the ones on attach_debugger_session and launch_debugger_session
async def list_debugger_sessions(
    project_path: Annotated[
        str | None,
        """
        The project path.
        In the case you know only the current working directory you can use it as the project path.
        In the case when it's unobvious which project to use you have to ASK the USER about which project to use.
        """,
    ] = None,
    timeout: Annotated[
        int, Field(description="Timeout in milliseconds to wait to get the sessions. Default: 30000.", ge=0),
    ] = 30000,
) -> SessionStatuses:
    """
    List all debug sessions for a given project.

    Use this to discover which debug sessions exist before operating on them.

    Preconditions:
    - At least one debug session must have been created via launch_debugger_session
      or attach_debugger_session for the given project_path.

    Behavior:
    - If project_path is specified, returns the status of all sessions associated with the project_path.
    - If project_path is not specified, returns the status of all sessions, system-wide.
    - Each status includes the session_id, current state (running/paused/stopped/unknown),
      debugee PID, and breakpoint mute status.
    - Stopped sessions are still listed. Refresh this list before reusing an old session_id,
      as sessions may have terminated.

    Next call guidance:
    - Pick a session_id from the results to use in other debugger tools.
    - If only one non-stopped session exists, you can omit session_id in most
      tool calls and the server will auto-select it.
    - Call this tool periodically to check if a session has stopped before
      attempting further operations.
    """
    normal_project_path: Path | None = None
    if project_path is not None:
        try:
            normal_project_path = normalize_file_path(project_path)
        except ValueError:
            raise AbsolutePathError("project_path")
    sessions = session_service.get_sessions(normal_project_path)
    async def go() -> SessionStatuses:
        return SessionStatuses(sessions=[await session.get_status() for session in sessions])

    return await wait_for_timeout(go(), timeout)
