from typing import Annotated, Any

from annotations import ProjectPath


def xdebug_set_variable(
    path: Annotated[
        list[str],
        "Path to target value, same format as `xdebug_get_value_by_path`. "
        "Use exact node names from the current paused `xdebug_get_frame_values` / `xdebug_get_value_by_path` output "
        "and refresh stale path tokens after the paused location changes."
    ],
    newValue: Annotated[
        str,
        "New value expression to assign. "
        "Pass raw expression text in the language of the current frame; "
        "it must be assignable to the target value by the debugger/evaluator. "
        "Do not pass JSON-escaped payloads or literal backslash-escaped quoted text."
    ],
    sessionId: Annotated[
        str | None,
        "Debug session ID. "
        "Use the current ID returned by `xdebug_get_debugger_status` or `xdebug_start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; "
        "if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
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
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'path': {
    #       'type': 'array',
    #       'items': {
    #         'type': 'string'
    #       },
    #       'description': 'Variable path used for mutation.'
    #     },
    #     'oldValue': {
    #       'type': 'string',
    #       'description': 'Value before mutation.'
    #     },
    #     'newValue': {
    #       'type': 'string',
    #       'description': 'Value after mutation.'
    #     },
    #     'applied': {
    #       'type': 'boolean',
    #       'description': 'Whether mutation was applied.'
    #     }
    #   },
    #   'required': [
    #     'path',
    #     'oldValue',
    #     'newValue',
    #     'applied'
    #   ],
    #   'type': 'object'
    # }
    """Mutates a variable value by path in the selected stack frame.
Use this tool to change state during debugging.

Preconditions:
- Session must be suspended.
- Value must be modifiable.
- `path` should come from the current paused `xdebug_get_frame_values` / `xdebug_get_value_by_path` output.

Path format is the same as in `xdebug_get_value_by_path`.
`newValue` must be a raw expression in the language of the current frame, and it must be assignable to the target value by the debugger/evaluator.
Do not pass JSON-escaped payloads or literal escape sequences such as `\\"text\\"`.

Result:
- Returns oldValue/newValue/applied.
- Unsupported mutation returns an error with a textual message.

Next call:
- Re-read value via `xdebug_get_value_by_path` or `xdebug_get_frame_values` to confirm."""
    print(sessionId)
    print(frameIndex)
    print(path)
    print(newValue)
    print(projectPath)
