from typing import Annotated, Any

from annotations import ProjectPath


def xdebug_get_stack(
    sessionId: Annotated[
        str | None,
        "Debug session ID. Use the current ID returned by `xdebug_get_debugger_status` or `xdebug_start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
        "If null and exactly one active session exists, it is selected automatically. "
        "If multiple sessions are active and sessionId is omitted, the call fails. Default: null."
    ] = None,
    threadId: Annotated[
        str | None,
        "Thread ID to get stack for. "
        "This value should come from `xdebug_get_threads` and matches the debugger thread display name, not an opaque numeric ID. "
        "If not specified, uses the current/active thread. Default: null."
    ] = None,
    limit: Annotated[int, "Max frames to return. Default: 200."] = 200,
    offset: Annotated[int, "Page offset. Default: 0."] = 0,
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'frames': {
    #       'type': 'array',
    #       'items': {
    #         'type': 'object',
    #         'required': [
    #           'presentation',
    #           'index',
    #           'isCurrent'
    #         ],
    #         'properties': {
    #           'presentation': {
    #             'type': 'string',
    #             'description': 'Rendered function/method frame label from debugger UI.'
    #           },
    #           'index': {
    #             'type': 'integer',
    #             'description': '0-based frame index to use as `frameIndex` in other debugger tools.'
    #           },
    #           'file': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Source file path as provided by the debugger when available.'
    #           },
    #           'line': {
    #             'type': [
    #               'integer',
    #               'null'
    #             ],
    #             'description': '1-based source line when available.'
    #           },
    #           'isCurrent': {
    #             'type': 'boolean',
    #             'description': 'Whether this is the currently selected frame.'
    #           }
    #         }
    #       },
    #       'description': 'Stack frames for the selected thread, ordered from top (index 0) to older frames.'
    #     },
    #     'threadId': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Thread identifier used to fetch this stack.'
    #     },
    #     'totalFrames': {
    #       'type': 'integer',
    #       'description': 'Total frame count for the stack.'
    #     }
    #   },
    #   'required': [
    #     'frames',
    #     'totalFrames'
    #   ],
    #   'type': 'object'
    # }
    """Returns the call stack for a thread in the debug session.
Use this tool to see the sequence of method calls that led to the current execution point.

Preconditions:
- Session must be suspended.

Behavior:
- `threadId` should come from `xdebug_get_threads` and matches the debugger thread display name (defaults to active thread).
- Includes frames even when source position is missing (file/line may be null).

Pagination:
- `offset`/`limit` are applied after collecting the full stack.

Frame fields include: index, file, line, isCurrent, presentation.
`file` is reported as provided by the debugger (no path normalization).

Next call:
- Use frame index from the current paused result in `xdebug_get_frame_values`, `xdebug_get_value_by_path`, or `xdebug_evaluate_expression`.
- Do not reuse a cached `frameIndex` after `RESUME`, `STEP_*`, `xdebug_run_to_line`, or any change in paused location."""
    print(sessionId)
    print(threadId)
    print(limit)
    print(offset)
    print(projectPath)

