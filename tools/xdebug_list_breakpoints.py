from typing import Annotated, Any


def xdebug_list_breakpoints(
    filePath: Annotated[
        str | None,
        "Optional file path to filter breakpoints. Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, archive entries like "
        "'/path/lib.jar!/pkg/Foo.class', and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools). "
        "If not specified, returns all breakpoints. Default: null."
    ] = None,
    sessionId: Annotated[
        str | None,
        "Debug session ID. Use the current ID returned by `xdebug_get_debugger_status` or `xdebug_start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
        "If null and exactly one active session exists, it is selected automatically. "
        "If multiple sessions are active and sessionId is omitted, the call fails. "
        "Default: null. Optional; when omitted, `breakpointsMuted` is returned only if exactly one active session exists."
    ] = None,
    projectPath: Annotated[
        str | None,
        " The project path. Pass this value ALWAYS if you are aware of it. It reduces numbers of ambiguous calls. \n "
        "In the case you know only the current working directory you can use it as the project path.\n "
        "If you're not aware about the project path you can ask user about it."
    ] = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'breakpoints': {
    #       'type': 'array',
    #       'items': {
    #         'type': 'object',
    #         'required': [
    #           'id',
    #           'type',
    #           'enabled',
    #           'owner',
    #           'isLogMessage',
    #           'isLogStack',
    #           'temporary',
    #           'suspendPolicy',
    #           'hitCount'
    #         ],
    #         'properties': {
    #           'id': {
    #             'type': 'string',
    #             'description': 'Canonical breakpoint ID (stable across list/remove).'
    #           },
    #           'type': {
    #             'type': 'string',
    #             'description': 'Breakpoint type (line/exception/other).'
    #           },
    #           'file': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'File path of the breakpoint as provided by the debugger (usually file URL).'
    #           },
    #           'line': {
    #             'type': [
    #               'integer',
    #               'null'
    #             ],
    #             'description': '1-based breakpoint line when available.'
    #           },
    #           'enabled': {
    #             'type': 'boolean',
    #             'description': 'Whether breakpoint is enabled.'
    #           },
    #           'owner': {
    #             'type': 'string',
    #             'enum': [
    #               'user',
    #               'agent'
    #             ],
    #             'description': 'Breakpoint ownership marker: `agent` if created/updated by MCP toolset, otherwise `user`.'
    #           },
    #           'condition': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Conditional expression for triggering breakpoint, if set.'
    #           },
    #           'logExpression': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Evaluate-and-log expression of the logpoint, if set (the value logged when the line is reached).'
    #           },
    #           'isLogMessage': {
    #             'type': 'boolean',
    #             'description': 'Whether breakpoint logs source position when hit.'
    #           },
    #           'isLogStack': {
    #             'type': 'boolean',
    #             'description': 'Whether breakpoint logs stack trace when hit.'
    #           },
    #           'temporary': {
    #             'type': 'boolean',
    #             'description': 'Whether breakpoint is temporary.'
    #           },
    #           'suspendPolicy': {
    #             'type': 'string',
    #             'description': 'Breakpoint suspend policy (all/thread/none).'
    #           },
    #           'hitCount': {
    #             'type': 'integer',
    #             'description': 'Breakpoint hit count, 0 when unavailable.'
    #           }
    #         }
    #       },
    #       'description': 'List of currently configured breakpoints.'
    #     },
    #     'totalCount': {
    #       'type': 'integer',
    #       'description': 'Total count.'
    #     },
    #     'enabledCount': {
    #       'type': 'integer',
    #       'description': 'Enabled count.'
    #     },
    #     'breakpointsMuted': {
    #       'type': 'boolean',
    #       'description': 'Whether breakpoints are globally muted for the resolved debugger session.'
    #     }
    #   },
    #   'required': [
    #     'breakpoints',
    #     'totalCount',
    #     'enabledCount'
    #   ],
    #   'type': 'object'
    # }
    """Lists all breakpoints in the project or in a specific file.
Use this tool to see all currently set breakpoints and their properties.

Tip: Call this before RESUME to confirm there is at least one enabled breakpoint that is expected to be hit next.

Behavior:
- If `filePath` is provided, returns only breakpoints in that file.
- Returns rich attributes for each breakpoint (id, type, file, line, enabled, owner, condition, isLogMessage, isLogStack, temporary, suspendPolicy, hitCount).
- `breakpointsMuted` reports the session-wide debugger mute flag when a session is resolved; it does not change per-breakpoint `enabled` values.

Next call:
- If no suitable breakpoint exists, call `xdebug_set_breakpoint`.
- Then continue execution with `xdebug_control_session(action=RESUME)` and `xdebug_control_session(action=WAIT_FOR_PAUSE)`."""
    print(filePath)
    print(sessionId)
    print(projectPath)
