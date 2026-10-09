from typing import Annotated

from annotations import FrameIndex, ProjectPath, SessionID


def get_frame_values(
    project_path: ProjectPath,
    session_id: SessionID = None,
    frame_index: FrameIndex = None,
    depth: Annotated[
        int,
        "Maximum depth for expanding nested objects "
        "(0 = no children (only frame variables), 1 = variables with first level children, 2 = two levels of children, etc.). "
        "Default: 0.",
    ] = 0,
) -> None:
    """Returns the values visible in the specified stack frame as a tree structure.
Use this tool to inspect local variables, parameters, and fields or other values available at a specific point in the call stack.

Preconditions:
- Session must be suspended.
- Frame index should come from the current paused `get_stack` result.

Format:
- Nodes that have children are marked with `+`.

Next call:
- Use `get_value_by_path` to drill into nested fields.
- Use `evaluate_expression` for computed checks in the same frame.
- Do not reuse a cached `frame_index` after `RESUME`, `STEP_*`, `run_to_line`, or any change in paused location."""
    print(session_id)
    print(frame_index)
    print(depth)
    print(project_path)
