from typing import Annotated, Any

from annotations import FrameIndex, ProjectPath, SessionID


def set_variable(
    path: Annotated[
        list[str],
        "Path to target value, same format as `get_value_by_path`. "
        "Use exact node names from the current paused `get_frame_values` / `get_value_by_path` output "
        "and refresh stale path tokens after the paused location changes."
    ],
    newValue: Annotated[
        str,
        "New value expression to assign. "
        "Pass raw expression text in the language of the current frame; "
        "it must be assignable to the target value by the debugger/evaluator. "
        "Do not pass JSON-escaped payloads or literal backslash-escaped quoted text."
    ],
    sessionId: SessionID = None,
    frameIndex: FrameIndex = None,
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
- `path` should come from the current paused `get_frame_values` / `get_value_by_path` output.

Path format is the same as in `get_value_by_path`.
`newValue` must be a raw expression in the language of the current frame, and it must be assignable to the target value by the debugger/evaluator.
Do not pass JSON-escaped payloads or literal escape sequences such as `\\"text\\"`.

Result:
- Returns oldValue/newValue/applied.
- Unsupported mutation returns an error with a textual message.

Next call:
- Re-read value via `get_value_by_path` or `get_frame_values` to confirm."""
    print(sessionId)
    print(frameIndex)
    print(path)
    print(newValue)
    print(projectPath)
