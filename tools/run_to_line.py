from typing import Annotated

from annotations import FilePath, LineNum, SessionID
from models import SessionStatus
import session_service
from utils import normalize_file_path


def run_to_line(
    file_path: FilePath,
    line: LineNum,
    session_id: SessionID = None,
    timeout: Annotated[int, "Timeout in milliseconds waiting for paused/stopped result. Default: 30000."] = 30000,
) -> SessionStatus:
    """
    Run execution until a specific file and line, then pause.

    Convenient shortcut to jump to a location without manually setting and
    removing a temporary breakpoint. Existing breakpoints are temporarily
    bypassed so only the target location triggers a pause.

    Preconditions:
    - A valid, non-stopped session must exist.
    - The target file and line must exist and point to executable code.

    Behavior:
    - Resumes execution, ignoring all existing breakpoints, until the target
      line is reached. Blocks until paused at that location or the session stops.
    - Preserves the session's previous breakpoint mute state.
    - Returns the session status showing the paused state and current position.

    Next call guidance:
    - After this call, the session is paused at the target line. Use `get_stack`
      and `list_variables` to inspect state at that location.
    - Use this instead of set_breakpoint + resume + wait_for_pause when you
      want to skip over existing breakpoints.
    - Not useful if you want to hit multiple breakpoints along the way — use
      the standard resume + wait_for_pause flow instead.
    - If the session is stopped, the program ran to completion.
      Create a new session instead of trying new calls on this one.
    """
    session = session_service.get_session(session_id)
    path = normalize_file_path(session.project_path, file_path)
    session.run_to_line(path, line)
    return session.get_status()
