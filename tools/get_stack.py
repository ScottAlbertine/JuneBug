from typing import Annotated

from pydantic import Field

from annotations import SessionID
from models import StackFrames
import session_service


def get_stack(
    session_id: SessionID = None,
    thread_id: Annotated[
        int | None,
        "Thread ID to get stack for. This value should come from `list_threads`. "
        "If not specified, uses the current/active thread. Default: null.",
    ] = None,
    limit: Annotated[int, Field(description="Max frames to return. Default: 200.", ge=1)] = 200,
    offset: Annotated[int, Field(description="Page offset. Default: 0.", ge=0)] = 0,
) -> StackFrames:
    """
    Returns the current function stack for a thread in the debug session.
    Use this tool to see the sequence of function calls that led to the current execution point.

    Behavior:
    - `thread_id` should come from `list_threads` (defaults to active thread).
    - Frames are sorted by most current first. The currently paused breakpoint is in the first frame returned.
    - Includes frames even when source position is missing (file/line may be null).

    Pagination:
    - `offset`/`limit` are applied after collecting the full stack.

    Frame fields include: id, name, file, line, library_code.
    `file` is reported as provided by the debugger (no path normalization).

    Next call:
    - Use frame `id` from the current paused result in `list_variables` or `evaluate_expression`.
    - Do not reuse a cached `frame_id` after `resume`, `step_*`, `run_to_line`, or any change in paused location.
    """

    session = session_service.get_session(session_id)
    return session.get_stack_trace(thread_id, limit, offset)
