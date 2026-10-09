from typing import Annotated

from annotations import ProjectPath, SessionID
from frontend_models import StackResponse


def get_stack(
    project_path: ProjectPath,
    session_id: SessionID = None,
    thread_id: Annotated[
        str | None,
        "Thread ID to get stack for. "
        "This value should come from `get_threads` and matches the debugger thread display name, not an opaque numeric ID. "
        "If not specified, uses the current/active thread. Default: null.",
    ] = None,
    limit: Annotated[int, "Max frames to return. Default: 200."] = 200,
    offset: Annotated[int, "Page offset. Default: 0."] = 0,
) -> StackResponse:
    """Returns the call stack for a thread in the debug session.
Use this tool to see the sequence of method calls that led to the current execution point.

Preconditions:
- Session must be suspended.

Behavior:
- `thread_id` should come from `get_threads` and matches the debugger thread display name (defaults to active thread).
- Includes frames even when source position is missing (file/line may be null).

Pagination:
- `offset`/`limit` are applied after collecting the full stack.

Frame fields include: index, file, line, is_current, presentation.
`file` is reported as provided by the debugger (no path normalization).

Next call:
- Use frame index from the current paused result in `get_frame_values`, `get_value_by_path`, or `evaluate_expression`.
- Do not reuse a cached `frame_index` after `RESUME`, `STEP_*`, `run_to_line`, or any change in paused location."""
    print(session_id)
    print(thread_id)
    print(limit)
    print(offset)
    print(project_path)
