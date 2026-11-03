from typing import Annotated

from pydantic import Field

from annotations import ExceptionType, SessionID
from enums import ExceptionBreakpointMode
from models import ExceptionBreakpoint
import session_service
from utils import wait_for_timeout


async def set_exception_breakpoint(
    exception_type: ExceptionType = "BaseException",
    mode: Annotated[
        ExceptionBreakpointMode,
        "Whether to break when the exception is raised, or only when it becomes unhandled. Default: unhandled.",
    ] = ExceptionBreakpointMode.UNHANDLED,
    session_id: SessionID = None,
    timeout: Annotated[
        int,
        Field(
            "Timeout in milliseconds waiting to set the exception breakpoint. "
            "This is *not* a timeout for the exception breakpoint to be hit. Default: 5000.",
            ge=0,
        ),
    ] = 5000,
) -> ExceptionBreakpoint:
    """
    Set an exception breakpoint to pause execution when a specific exception is raised or becomes unhandled.

    Each call registers a new exception breakpoint. Setting the same exception type with the same mode again is a no-op.
    The breakpoint takes effect immediately unless breakpoints are globally muted.

    Preconditions:
    - A valid, non-stopped session must exist.
    - The exception_type must be a valid Python exception class name. Use 'BaseException' to break on any exception,
      or a fully qualified name like 'pkg.module.MyError' for a specific type.

    Behavior:
    - Returns an ExceptionBreakpoint object with the registered exception type and mode.
    - The mode parameter controls when the breakpoint triggers:
      - 'raised': Break whenever the exception is raised.
      - 'unhandled' (default): Break when the process is exiting due to unhandled exception.
      - 'user_unhandled': Break when the exception escapes into library code.
    - If breakpoints are muted, the breakpoint is registered but won't trigger until breakpoints are unmuted.
    - This is a global breakpoint: it applies to all threads and all files in the session.

    Next call guidance:
    - After setting exception breakpoints, call control_debugger_session with action "resume" to start execution.
      The debugger will pause when an exception matches the breakpoint criteria.
    - Use wait_for_pause after resume to block until the exception breakpoint is triggered.
    - Use list_breakpoints to verify the exception breakpoint was registered.
    - Use remove_exception_breakpoint to remove it when no longer needed.
    """
    session = session_service.get_session(session_id)
    return await wait_for_timeout(session.set_exception_breakpoint(exception_type, mode), timeout)
