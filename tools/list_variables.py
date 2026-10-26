from typing import Annotated

from pydantic import Field

from annotations import FrameID, SessionID, ShowHidden
from models import Variables
import session_service

DEPTH_DESCRIPTION = """
    Maximum depth for expanding nested objects
    (0 = no children (only frame variables), 1 = variables with first level children, 2 = two levels of children, etc.). "
    Maximum allowed depth is 4, which returns 9MB of data from a typical Python process.
    Be very careful not to flood your context with this.
    Default: 0.
"""

async def list_variables(
    session_id: SessionID = None,
    frame_id: FrameID = None,
    show_hidden: ShowHidden = False,
    depth: Annotated[int, Field(description=DEPTH_DESCRIPTION, ge=0, le=4)] = 0,
) -> Variables:
    """
    List variables visible in a stack frame's scope.

    Returns local variables, global variables, function parameters, and other values from the selected frame.

    Preconditions:
    - The session must be in a paused state.

    Behavior:
    - If frame_id is omitted, uses the top frame of the current thread's stack.
    - `show_hidden` controls whether dunder variables, classes, functions, and
      other normally hidden symbols are included.
    - `depth` controls recursive expansion of nested objects (dicts, lists,
      objects with attributes). 0 = variables only, no children. 1 = first level
      of children. Up to 4 is allowed (depth 4 can return ~9MB for a typical
      Python process — use sparingly).
    - Each variable shows its name, value, type, and optional children array.
    - A variable's `evaluate_name`, if present, can be used directly in `evaluate_expression`.

    Next call guidance:
    - For deeper inspection of a specific variable, call this tool again with
      a higher `depth` value, or use `evaluate_expression` on a variable's
      `evaluate_name` to drill into it.
    - Re-fetch variables after stepping, as the frame context changes.
    - Do not reuse a cached frame_id after resume/step — get a fresh one from
      `get_stack` first.
    """
    session = session_service.get_session(session_id)
    variables = await session.list_variables(frame_id, show_hidden, depth)
    return Variables(variables=variables)
