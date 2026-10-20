from typing import Annotated

from pydantic import Field

from annotations import FrameID, SessionID, ShowHidden
from models import Variable
import session_service

DEPTH_DESCRIPTION = """
    Maximum depth for expanding children of the evaluated result
    (0 = value only, 1 = immediate children, 2 = children + grandchildren, etc.). Default: 0.
"""


def evaluate_expression(
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
    Evaluates an expression in the context of the given stack frame.
    Use this tool to compute values, call methods, or inspect expressions during debugging.

    Preconditions:
    - Session must be suspended.
    - Evaluation must be supported for the selected frame/language.
    - `expression` must be a valid expression in the language of the current frame.

    The result is returned as:
    - depth == 0: just the result of the evaluated expression
    - depth > 0: the presentation plus any children, like `list_variables` does

    Input rules:
    - Pass raw expression text exactly as the debugger evaluator should parse it.
    - Do not pass JSON-escaped payloads or literal escape sequences such as `\\"text\\"`.
    - Recommended to pass the `evaluate_name` from the result of a `list_variables` tool call.

    Next call:
    - If expression confirms hypothesis, continue with `control_debugger_session(step_*|resume)`.
    - If more detail is needed, inspect related values via further `evaluate_expression` calls.
    """
    session = session_service.get_session(session_id)
    return session.evaluate_expression(expression, frame_id, show_hidden, depth)
