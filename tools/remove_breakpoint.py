from annotations import FilePath, LineNum, SessionID
import session_service
from utils import normalize_file_path


def remove_breakpoint(file_path: FilePath, line: LineNum, session_id: SessionID = None) -> None:
    """
    Remove a breakpoint at a specific file and line number.

    Idempotent operation — calling this on a location with no breakpoint is a no-op.

    Preconditions:
    - A valid, non-stopped session must exist.

    Behavior:
    - The breakpoint at the given location will no longer trigger.
    - If breakpoints are muted, the removal takes effect immediately (the breakpoint
      simply won't be restored when unmuted).
    - Returns nothing on success.

    Next call guidance:
    - Use list_breakpoints to verify the breakpoint was removed.
    """
    session = session_service.get_session(session_id)
    path = normalize_file_path(session.project_path, file_path)
    session.remove_breakpoint(path, line)
