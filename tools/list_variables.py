from typing import Annotated

from pydantic import Field

from annotations import FrameID, SessionID
from models import Variables
import session_service


def list_variables(
    session_id: SessionID = None,
    frame_id: FrameID = None,
    show_hidden: Annotated[
        bool,
        "List all variables, including ones that are normally hidden, like __dunder_variables__, Classes, functions, etc. "
        "Default: False",
    ] = False,
    depth: Annotated[
        int,
        Field(
            description="""
                Maximum depth for expanding nested objects
                (0 = no children (only frame variables), 1 = variables with first level children, 2 = two levels of children, etc.). "
                Maximum allowed depth is 4, which returns 9MB of data from a typical Python process.
                Be very careful not to flood your context with this.
                Default: 0.
            """,
            ge=0,
            le=4,
        ),
    ] = 0,
) -> Variables:
    """
    Returns the variables visible in the specified stack frame as a tree structure.
    Use this tool to inspect local variables, parameters, and fields or other values available at a specific point in the call stack.

    Preconditions:
    - Session must be suspended.
    - Frame index should come from the current paused `get_stack` result.

    Behavior:
    - The `children` property of a variable is `null` if the variable has no children.
    - An empty list `[]` of children means that the variable may have children, but they have not been omitted to avoid flooding your context window.

    Next call:
    - Use `get_value_by_path` to drill into nested fields.
    - Use `evaluate_expression` for computed checks in the same frame.
    - Do not reuse a cached `frame_id` after `resume`, `step_*`, `run_to_line`, or any change in paused location.
    """
    session = session_service.get_session(session_id)
    if frame_id is None:
        thread_id = session.get_current_thread_id()  # update state before asserting it, should save some calls sometimes
        frame_id = session.list_stack_frames(thread_id)[0].id
    variables = session.list_variables(frame_id, show_hidden, depth)
    return Variables(variables=variables)
