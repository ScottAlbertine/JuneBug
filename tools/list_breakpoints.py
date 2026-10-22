from typing import Annotated

from annotations import SessionID
from models import BreakpointsResponse
import session_service
from utils import normalize_file_path


def list_breakpoints(
    session_id: SessionID = None,
    file_path: Annotated[
        str | None,
        "Path to the file. Supports project-relative paths, paths with '..', absolute paths, and URLs such as 'file://'. "
        "If not specified, returns all breakpoints. Default: null.",
    ] = None,
) -> BreakpointsResponse:
    """
    List all configured breakpoints in a debug session, optionally filtered by file.

    Returns breakpoints sorted by file path, then by line number. Each breakpoint
    includes its location, source line text, condition, temporary flag, and hit count.

    Preconditions:
    - A valid, non-stopped session must exist.

    Behavior:
    - If file_path is provided, returns only breakpoints in that file.
    - If file_path is omitted, returns all breakpoints across all files.
    - The response includes the session's breakpoint mute status so you know whether
      breakpoints are currently active or dormant.
    - Hit count shows how many times each breakpoint has been triggered (0 if never hit).

    Next call guidance:
    - Use the returned breakpoint locations to understand where the debugee will pause.
    - If breakpoints_muted is true, the breakpoints exist but won't trigger until unmuted.
    - Check hit_count to verify breakpoints were actually hit during execution.
    """
    session = session_service.get_session(session_id)
    path = normalize_file_path(file_path, session.project_path) if file_path else None
    breakpoints = session.list_breakpoints(path)
    return BreakpointsResponse(breakpoints=breakpoints, breakpoints_muted=session.breakpoints_muted)
