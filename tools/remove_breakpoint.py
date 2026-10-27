from typing import Annotated

from pydantic import Field

from annotations import FilePath, LineNum, SessionID
import session_service
from utils import normalize_file_path, wait_for_timeout


async def remove_breakpoint(
    file_path: FilePath,
    line: LineNum,
    session_id: SessionID = None,
    timeout: Annotated[
        int, Field(description="Timeout in milliseconds to wait to remove the breakpoint. Default: 5000.", ge=0),
    ] = 5000,
) -> None:
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
    path = normalize_file_path(file_path, session.project_path)
    await wait_for_timeout(session.remove_breakpoint(path, line), timeout)
