from typing import Annotated

from annotations import ProjectPath


def xdebug_get_frame_values(
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
        "If null, uses the frame currently selected in the debugger, the one `xdebug_get_stack` marks `isCurrent`. "
        "Default: null."
    ] = None,
    depth: Annotated[
        int,
        "Maximum depth for expanding nested objects "
        "(0 = no children (only frame variables), 1 = variables with first level children, 2 = two levels of children, etc.). "
        "Default: 0."
    ] = 0,
    projectPath: ProjectPath = None,
) -> None:
    """Returns the values visible in the specified stack frame as a tree structure.
Use this tool to inspect local variables, parameters, and fields or other values available at a specific point in the call stack.

Preconditions:
- Session must be suspended.
- Frame index should come from the current paused `xdebug_get_stack` result.

Format:
- Nodes that have children are marked with `+`.

Next call:
- Use `xdebug_get_value_by_path` to drill into nested fields.
- Use `xdebug_evaluate_expression` for computed checks in the same frame.
- Do not reuse a cached `frameIndex` after `RESUME`, `STEP_*`, `xdebug_run_to_line`, or any change in paused location."""
    print(sessionId)
    print(frameIndex)
    print(depth)
    print(projectPath)

