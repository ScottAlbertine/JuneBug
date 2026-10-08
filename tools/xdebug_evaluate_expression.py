from typing import Annotated


def xdebug_evaluate_expression(
    expression: Annotated[
        str,
        "Expression to evaluate in the current context. "
        "Pass raw expression text in the language of the current frame; "
        "do not pass JSON-escaped payloads or literal backslash-escaped quoted text."
    ],
    sessionId: Annotated[
        str | None,
        "Debug session ID. Use the current ID returned by `xdebug_get_debugger_status` or `xdebug_start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
        "If null and exactly one active session exists, it is selected automatically. "
        "If multiple sessions are active and sessionId is omitted, the call fails. Default: null."
    ] = None,
    frameIndex: Annotated[
        int | None,
        "Stack frame index counted from the top of the stack, the same `index` `xdebug_get_stack` reports: "
        "0 is the frame execution is in, 1 its caller, and so on. "
        "Obtain this from the current paused `xdebug_get_stack` result; "
        "do not reuse a cached frame index after `RESUME`, `STEP_*`, `xdebug_run_to_line`, or any change in paused location. "
        "If null, uses the frame currently selected in the debugger, the one `xdebug_get_stack` marks `isCurrent`. Default: null."
    ] = None,
    depth: Annotated[
        int,
        "Maximum depth for expanding children of the evaluated result "
        "(0 = value only, 1 = immediate children, 2 = children + grandchildren, etc.). Default: 0."
    ] = 0,
    projectPath: Annotated[
        str | None,
        " The project path. Pass this value ALWAYS if you are aware of it. It reduces numbers of ambiguous calls. \n "
        "In the case you know only the current working directory you can use it as the project path.\n "
        "If you're not aware about the project path you can ask user about it."
    ] = None,
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
- If expression confirms hypothesis, continue with `xdebug_control_session(STEP_*|RESUME)`.
- If more detail is needed, inspect related values via `xdebug_get_frame_values` / `xdebug_get_value_by_path`."""
    print(sessionId)
    print(frameIndex)
    print(expression)
    print(depth)
    print(projectPath)
