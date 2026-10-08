from typing import Annotated, Any

from annotations import ProjectPath
from enums import SuspendPolicy


def set_breakpoint(
    breakpointId: Annotated[
        str | None,
        "Canonical breakpoint ID returned by `set_breakpoint` or `list_breakpoints`. "
        "If provided, the tool runs in ID mode. "
        "Omit this or pass null in location mode; do not use placeholder strings such as empty string or fake path-like values. "
        "Default: null."
    ] = None,
    sessionId: Annotated[
        str | None,
        "Debug session ID. Use the current ID returned by `get_debugger_status` or `start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
        "If null and exactly one active session exists, it is selected automatically. "
        "If multiple sessions are active and sessionId is omitted, the call fails. "
        "Default: null. "
        "Use with `breakpointsMuted` in a dedicated mute-only call; do not combine that call with breakpoint target or settings parameters."
    ] = None,
    filePath: Annotated[
        str | None,
        "Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, archive entries like '/path/lib.jar!/pkg/Foo.class', "
        "and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools). "
        "Required only in location mode. Optional in ID mode to relocate line breakpoints."
    ] = None,
    line: Annotated[
        int | None,
        "1-based line number. Required only in location mode. Optional in ID mode to relocate line breakpoints."
    ] = None,
    condition: Annotated[
        str | None,
        "Optional condition expression - breakpoint will only trigger when this evaluates to true. "
        "Validation errors are reported asynchronously via control_session(...).breakpointErrorsTail (JVM-based debuggers only). "
        "Default: null."
    ] = None,
    logExpression: Annotated[
        str | None,
        "The Evaluate-and-log expression. "
        "When set, its result is logged each time the breakpoint is hit, read via control_session(action=DRAIN_EVENTS).tracepointOutputsTail. "
        "Combine with suspendPolicy=NONE to make a non-suspending logpoint - the preferred, most important way to capture runtime values without freezing threads. "
        "Keep it side-effect-free (no mutation, I/O, or iterator/stream advancement). logExpression=null clears it. "
        "Default: null."
    ] = None,
    isLogMessage: Annotated[
        bool,
        "Whether to log breakpoint hit position (source location) when breakpoint is reached. "
        "In JVM-based debuggers output is available via control_session(action=DRAIN_EVENTS).tracepointOutputsTail. "
        "Default: false."
    ] = False,
    isLogStack: Annotated[
        bool,
        "Whether to log stack trace when breakpoint is reached. "
        "In JVM-based debuggers output is available via control_session(action=DRAIN_EVENTS).tracepointOutputsTail. "
        "Default: false."
    ] = False,
    temporary: Annotated[bool, "Temporary breakpoint (removed after first hit). Default: false."] = False,
    suspendPolicy: Annotated[SuspendPolicy, "Suspend policy: ALL, THREAD, NONE. Default: ALL."] = SuspendPolicy.ALL,
    enabled: Annotated[bool, "Whether breakpoint is enabled. Default: true."] = True,
    breakpointsMuted: Annotated[
        bool | None,
        "Session-wide breakpoint mute flag. "
        "When provided, call this tool with only `sessionId` plus `breakpointsMuted`; "
        "do not pass breakpointId, filePath, line, condition, logging, suspend, temporary, or enabled parameters. "
        "Default: null."
    ] = None,
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'breakpointId': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Canonical breakpoint ID. Absent for breakpoint mute-only operations.'
    #     },
    #     'previousBreakpointId': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Previous canonical breakpoint ID when operation relocated an existing line breakpoint.'
    #     },
    #     'added': {
    #       'type': [
    #         'object',
    #         'null'
    #       ],
    #       'required': [
    #         'id',
    #         'type',
    #         'enabled',
    #         'owner',
    #         'isLogMessage',
    #         'isLogStack',
    #         'temporary',
    #         'suspendPolicy',
    #         'hitCount'
    #       ],
    #       'properties': {
    #         'id': {
    #           'type': 'string',
    #           'description': 'Canonical breakpoint ID (stable across list/remove).'
    #         },
    #         'type': {
    #           'type': 'string',
    #           'description': 'Breakpoint type (line/exception/other).'
    #         },
    #         'file': {
    #           'type': [
    #             'string',
    #             'null'
    #           ],
    #           'description': 'File path of the breakpoint as provided by the debugger (usually file URL).'
    #         },
    #         'line': {
    #           'type': [
    #             'integer',
    #             'null'
    #           ],
    #           'description': '1-based breakpoint line when available.'
    #         },
    #         'enabled': {
    #           'type': 'boolean',
    #           'description': 'Whether breakpoint is enabled.'
    #         },
    #         'owner': {
    #           'type': 'string',
    #           'enum': [
    #             'user',
    #             'agent'
    #           ],
    #           'description': 'Breakpoint ownership marker: `agent` if created/updated by MCP toolset, otherwise `user`.'
    #         },
    #         'condition': {
    #           'type': [
    #             'string',
    #             'null'
    #           ],
    #           'description': 'Conditional expression for triggering breakpoint, if set.'
    #         },
    #         'logExpression': {
    #           'type': [
    #             'string',
    #             'null'
    #           ],
    #           'description': 'Evaluate-and-log expression of the logpoint, if set (the value logged when the line is reached).'
    #         },
    #         'isLogMessage': {
    #           'type': 'boolean',
    #           'description': 'Whether breakpoint logs source position when hit.'
    #         },
    #         'isLogStack': {
    #           'type': 'boolean',
    #           'description': 'Whether breakpoint logs stack trace when hit.'
    #         },
    #         'temporary': {
    #           'type': 'boolean',
    #           'description': 'Whether breakpoint is temporary.'
    #         },
    #         'suspendPolicy': {
    #           'type': 'string',
    #           'description': 'Breakpoint suspend policy (all/thread/none).'
    #         },
    #         'hitCount': {
    #           'type': 'integer',
    #           'description': 'Breakpoint hit count, 0 when unavailable.'
    #         }
    #       },
    #       'description': 'Details of the newly added or updated breakpoint. Absent for breakpoint mute-only operations.'
    #     },
    #     'totalBreakpoints': {
    #       'type': 'integer',
    #       'description': 'Current total number of breakpoints after operation.'
    #     },
    #     'lineText': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Short excerpt of the actual source line where the breakpoint resides, truncated when needed. Present for line breakpoints only.'
    #     },
    #     'breakpointsMuted': {
    #       'type': 'boolean',
    #       'description': 'Whether breakpoints are globally muted for the resolved debugger session.'
    #     },
    #     'message': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Additional note when requested and actual positions differ.'
    #     }
    #   },
    #   'required': [
    #     'totalBreakpoints'
    #   ],
    #   'type': 'object'
    # }
    """Creates or updates a breakpoint or a logpoint (a non-suspending "Evaluate and log" breakpoint).
Use this tool to set line breakpoints, set logpoints via `logExpression`, update existing breakpoints by ID, and control tracepoint/logging behavior.

Logpoints are the preferred, low-disturbance probe, and providing a `logExpression` is the most important input:
set `logExpression` together with `suspendPolicy=NONE` to evaluate an expression and log its result every time the line
is reached WITHOUT stopping execution — the primary way to capture runtime values, branch/reachability evidence, counts,
and identifiers. Read the logged output via `control_session(action=DRAIN_EVENTS).tracepointOutputsTail`.

Targeting modes:
- By location: provide `filePath` + `line`, and omit `breakpointId` (or pass null). Do not use placeholder strings such as `""`, `"/"`, or `"__omit__"`.
- By ID: provide an existing opaque canonical `breakpointId` returned by `set_breakpoint` or `list_breakpoints` (optional `filePath`/`line` can relocate line breakpoints).
- Breakpoint mute-only: provide only `sessionId` and `breakpointsMuted`.
  Do not combine `breakpointsMuted` with breakpoint target or settings parameters.

Validation:
- In location mode, both `filePath` and `line` are required.
- In ID mode, breakpoint must exist and be uniquely identified by `breakpointId`.
- In location mode, `filePath` is relative to the project root, `line` is 1-based, and the target location must be executable.
- In breakpoint mute-only mode, a debugger session must be resolved from `sessionId` or the single active session.

Event reporting:
- Invalid `condition` expressions are reported asynchronously via `control_session(...).breakpointErrorsTail`.
- Tracepoint output from breakpoints with `isLogMessage` and/or `isLogStack` is drained via `control_session(action=DRAIN_EVENTS).tracepointOutputsTail`.
- Breakpoint-error and tracepoint-output reporting is currently supported only by JVM-based debuggers (Java, Kotlin, etc.).
- A successful `set_breakpoint` response does not guarantee that `condition` or tracepoint expressions are valid; check later `breakpointErrorsTail` before relying on them.
- Successful line-breakpoint responses also include `lineText`, a truncated excerpt of the actual source line where the breakpoint now resides. Inspect it to confirm placement before resuming.

Apply semantics:
- Provided fields are applied as the resulting state for the target breakpoint.
- `condition=null` clears existing condition.
- `logExpression` sets the Evaluate-and-log expression that is evaluated and logged when the breakpoint is hit; `logExpression=null` clears it. Combine with `suspendPolicy=NONE` for a non-suspending logpoint (the preferred way to capture values). Keep it side-effect-free; evaluation errors surface in `breakpointErrorsTail`.
- `isLogMessage=true` logs breakpoint hit position.
- `isLogStack=true` logs current stack trace.
- If both flags are true, both position and stack are logged.
- With `isLogMessage`/`isLogStack` + `suspendPolicy=NONE`, the breakpoint behaves as a tracepoint.
- In ID mode, if `filePath`/`line` are provided for a line breakpoint, it is relocated (recreated) at the new location.
- In ID mode, for non-line breakpoints, `filePath`/`line` are ignored and reported in `message`.
- `breakpointsMuted` is a session-wide debugger flag; use it in a dedicated call with only `sessionId` and `breakpointsMuted`.
  It does not change the per-breakpoint `enabled` value.
- Any successful operation marks breakpoint as `agent` ownership (`mcpBreakpointMarker`).

Next call:
- Use returned `lineText` and/or `list_breakpoints` to verify placement.
- Start/continue execution via `start_debugger_session` or `control_session(action=RESUME)`."""
    print(breakpointId)
    print(sessionId)
    print(filePath)
    print(line)
    print(condition)
    print(logExpression)
    print(isLogMessage)
    print(isLogStack)
    print(temporary)
    print(suspendPolicy)
    print(enabled)
    print(breakpointsMuted)
    print(projectPath)

