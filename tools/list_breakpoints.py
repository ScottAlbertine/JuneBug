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
    Lists all breakpoints in the project or in a specific file.
    Use this tool to see all currently set breakpoints and their properties.

    Tip: Call this before `resume` or `wait_for_pause` to confirm there is at least one enabled breakpoint that is expected to be hit next.

    Behavior:
    - If `file_path` is provided, returns only breakpoints in that file.
    - Returns rich attributes for each breakpoint (type, file, line, condition, temporary, suspend_policy, hit_count).
    - `breakpoints_muted` reports the session-wide debugger mute flag.

    Next call:
    - If no suitable breakpoint exists, call `set_breakpoint`.
    - Then continue execution with `control_session(action=resume)` or `control_session(action=wait_for_pause)`.
    """
    session = session_service.get_session(session_id)
    path = normalize_file_path(session.project_path, file_path) if file_path else None
    breakpoints = session.list_breakpoints(path)
    return BreakpointsResponse(breakpoints=breakpoints, breakpoints_muted=session.breakpoints_muted)
