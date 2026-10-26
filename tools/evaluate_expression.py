from typing import Annotated

from pydantic import Field

from annotations import FrameID, SessionID, ShowHidden
from models import Variable
import session_service

DEPTH_DESCRIPTION = """
    Maximum depth for expanding children of the evaluated result
    (0 = value only, 1 = immediate children, 2 = children + grandchildren, etc.). Default: 0.
"""


async def evaluate_expression(
    expression: Annotated[
        str,
        "Expression to evaluate in the given frame. "
        "Pass raw expression text in the language of the current frame; "
        "do not pass JSON-escaped payloads or literal backslash-escaped quoted text.",
    ],
    session_id: SessionID = None,
    frame_id: FrameID = None,
    show_hidden: ShowHidden = False,
    depth: Annotated[int, Field(description=DEPTH_DESCRIPTION, ge=0, le=4)] = 0,
) -> Variable:
    """
    Evaluate a Python expression in the context of a stack frame.

    Executes the given expression using the variables and scope of the selected
    frame. Useful for inspecting computed values, drilling into objects, calling methods,
    or testing hypotheses about program state.

    Preconditions:
    - The session must be in a paused state.
    - If frame_id is not provided, the top frame of the current thread is used.

    Behavior:
    - Evaluates the raw Python expression in the target frame's scope.
    - Returns the result as a Variable with name (the expression), value, type,
      and optional children (if `depth > 0`).
    - `depth` controls recursive expansion of the result object, same as
      `list_variables`. 0 returns the value only; higher values expand children.
    - `show_hidden` includes hidden attributes (dunders, etc.) in child expansion.
    - If the expression raises an exception, the tool call returns the exception as a Variable.
    - Frame IDs become stale after stepping or resuming — always get a fresh
      frame_id from `get_stack` before evaluating.

    Next call guidance:
    - Use the returned Variable's children to inspect nested structures.
    - If you need to evaluate something in a different frame, get that frame's
      id from `get_stack` first, then call this tool with the new frame_id.
    - For simple variable inspection, `list_variables` is often sufficient;
      use this tool for computed expressions or when you need a specific value.
    """
    session = session_service.get_session(session_id)
    return await session.evaluate_expression(expression, frame_id, show_hidden, depth)
