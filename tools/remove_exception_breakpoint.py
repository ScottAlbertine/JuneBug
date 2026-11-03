from typing import Annotated

from pydantic import Field

from annotations import ExceptionType, SessionID
from enums import ExceptionBreakpointMode
import session_service
from utils import wait_for_timeout


async def remove_exception_breakpoint(
    exception_type: ExceptionType = "BaseException",
    mode: Annotated[
        ExceptionBreakpointMode,
        "Whether to break when the exception is raised, or only when it becomes unhandled. Default: unhandled.",
    ] = ExceptionBreakpointMode.UNHANDLED,
    session_id: SessionID = None,
    timeout: Annotated[
        int,
        Field(description="Timeout in milliseconds to wait to remove the exception breakpoint. Default: 5000.", ge=0),
    ] = 5000,
) -> None:
    """
    Remove an exception breakpoint that was previously registered with set_exception_breakpoint.

    Idempotent operation — calling this on an exception type and mode that has no registered breakpoint is a no-op.

    Preconditions:
    - A valid, non-stopped session must exist.
    - The exception_type and mode must exactly match what is shown on an existing exception breakpoint.

    Behavior:
    - The exception breakpoint matching both the given exception_type and mode is removed.
    - If breakpoints are muted, the removal takes effect immediately (the breakpoint
      simply won't be restored when unmuted).
    - Returns nothing on success.

    Next call guidance:
    - Use list_breakpoints to verify the exception breakpoint was removed.
    """
    session = session_service.get_session(session_id)
    await wait_for_timeout(session.remove_exception_breakpoint(exception_type, mode), timeout)
