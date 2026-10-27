from typing import Annotated

from pydantic import Field

from annotations import SessionID
from models import StackFrames
import session_service
from utils import wait_for_timeout


async def get_stack(
    session_id: SessionID = None,
    thread_id: Annotated[
        int | None,
        "Thread ID to get stack for. This value should come from `list_threads`. "
        "If not specified, uses the current/active thread. Default: null.",
    ] = None,
    limit: Annotated[int, Field(description="Max frames to return. Default: 200.", ge=1)] = 200,
    offset: Annotated[int, Field(description="Page offset. Default: 0.", ge=0)] = 0,
    timeout: Annotated[
        int, Field(description="Timeout in milliseconds to wait for getting the stack. Default: 5000.", ge=0),
    ] = 5000,
) -> StackFrames:
    """
    Get the call stack (stack trace) for a thread in the debug session.

    Shows the chain of function calls leading to the current execution point,
    from the most recent (top of stack, index 0) to older frames.

    Preconditions:
    - A valid, non-stopped session must exist.
    - If thread_id is not provided, there must be a current thread (set when
      the session paused or stepped).

    Behavior:
    - If thread_id is omitted, uses the currently selected thread (the one that
      last triggered a pause event).
    - Returns frames ordered from top (current execution point) to bottom (entry).
    - Each frame includes its id (for use with `list_variables`), function name,
      source file path, line number, and whether it is library code.
    - Supports pagination via `offset` and `limit`. `total_frames` shows the
      full stack depth for pagination math.
    - Fast (~20ms) on paused threads; slow (~600ms) on running threads. Avoid
      calling on running threads unless necessary.

    Next call guidance:
    - Use a frame's `id` with `list_variables` to inspect local and closure
      variables in that frame's scope.
    - Use a frame's `id` with `evaluate_expression` to run code in that context.
    - Skip frames marked `library_code: true` unless you need to debug into libs.
    """
    session = session_service.get_session(session_id)
    return await wait_for_timeout(session.get_stack_trace(thread_id, limit, offset), timeout)
