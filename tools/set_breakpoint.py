from typing import Annotated

from annotations import FilePath, LineNum, SessionID
from models import Breakpoint
import session_service
from utils import normalize_file_path


async def set_breakpoint(
    file_path: FilePath,
    line: LineNum,
    session_id: SessionID = None,
    condition: Annotated[
        str | None,
        "Optional condition expression - breakpoint will only trigger when this evaluates to true. Default: null.",
    ] = None,
    temporary: Annotated[bool, "Temporary breakpoint (removed after first hit). Default: false."] = False,
) -> Breakpoint:
    """
    Set a breakpoint at a specific file and line number in a debug session.

    Each call registers a new breakpoint or updates an existing one at the same location.
    The breakpoint takes effect immediately unless breakpoints are globally muted.

    Preconditions:
    - A valid, non-stopped session must exist.
    - The file_path must resolve to an existing file.
    - The line number must be within the file and point to executable code.

    Behavior:
    - Returns a Breakpoint object with the location and source line text.
    - If breakpoints are muted, the breakpoint is registered but won't trigger
      until breakpoints are unmuted.
    - The condition parameter allows a Python expression; the breakpoint only
      triggers when the expression evaluates to true.
    - The temporary parameter creates a one-hit breakpoint (auto-removed after first hit).

    Next call guidance:
    - After setting breakpoints, call control_debugger_session with action "resume"
      to start execution. The debugger will pause when the breakpoint is hit.
    - Use wait_for_pause after resume to block until the breakpoint is triggered.
    - Use list_breakpoints to verify the breakpoint was registered.
    """
    session = session_service.get_session(session_id)
    path = normalize_file_path(file_path, session.project_path)
    return await session.set_breakpoint(path, line, temporary, condition)
