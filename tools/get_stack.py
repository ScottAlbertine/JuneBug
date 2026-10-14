from typing import Annotated

from annotations import SessionID
from models import StackResponse
import session_service


def get_stack(
    session_id: SessionID = None,
    thread_id: Annotated[
        int | None,
        "Thread ID to get stack for. This value should come from `list_threads`. "
        "If not specified, uses the current/active thread. Default: null.",
    ] = None,
    limit: Annotated[int, "Max frames to return. Default: 200."] = 200,
    offset: Annotated[int, "Page offset. Default: 0."] = 0,
) -> StackResponse:
    """
    Returns the call stack for a thread in the debug session.
    Use this tool to see the sequence of method calls that led to the current execution point.

    Preconditions:
    - Session must be paused.

    Behavior:
    - `thread_id` should come from `list_threads` (defaults to active thread).
    - Frames are sorted by most current first. The currently paused breakpoint is in the first frame returned.
    - Includes frames even when source position is missing (file/line may be null).

    Pagination:
    - `offset`/`limit` are applied after collecting the full stack.

    Frame fields include: id, name, line, column, file.
    `file` is reported as provided by the debugger (no path normalization).

    Next call:
    - Use frame id from the current paused result in `list_frame_values`, `get_value_by_path`, or `evaluate_expression`.
    - Do not reuse a cached `frame_id` after `resume`, `step_*`, `run_to_line`, or any change in paused location.
    """

    session = session_service.get_session(session_id)
    if not thread_id:
        thread_id = session.get_current_thread_id()
    frames = session.list_stack_frames(thread_id)
    return StackResponse(frames=frames[offset:offset + limit], thread_id=thread_id, total_frames=len(frames))
