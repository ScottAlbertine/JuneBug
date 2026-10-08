from typing import Annotated

from annotations import FrameIndex, ProjectPath, SessionID


def evaluate_expression(
    projectPath: ProjectPath,
    expression: Annotated[
        str,
        "Expression to evaluate in the current context. "
        "Pass raw expression text in the language of the current frame; "
        "do not pass JSON-escaped payloads or literal backslash-escaped quoted text.",
    ],
    sessionId: SessionID = None,
    frameIndex: FrameIndex = None,
    depth: Annotated[
        int,
        "Maximum depth for expanding children of the evaluated result "
        "(0 = value only, 1 = immediate children, 2 = children + grandchildren, etc.). Default: 0.",
    ] = 0,
) -> None:
    """Evaluates an expression in the context of the current stack frame.
Use this tool to compute values, call methods, or inspect expressions during debugging.

Preconditions:
- Session must be suspended.
- Evaluation must be supported for the selected frame/language.
- `expression` must be a valid expression in the language of the current frame.

The result is returned as:
- depth == 0: just the presentation of the evaluated expression
- depth > 0: the presentation plus a pseudo-graphics tree of its children up to the requested depth

Input rules:
- Pass raw expression text exactly as the debugger evaluator should parse it.
- Do not pass JSON-escaped payloads or literal escape sequences such as `\\"text\\"`.

Next call:
- If expression confirms hypothesis, continue with `control_session(STEP_*|RESUME)`.
- If more detail is needed, inspect related values via `get_frame_values` / `get_value_by_path`."""
    print(sessionId)
    print(frameIndex)
    print(expression)
    print(depth)
    print(projectPath)
