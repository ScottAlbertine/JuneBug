from typing import Annotated, Any

from annotations import ProjectPath
from enums import ActionEnum


def xdebug_control_session(
    action: Annotated[
        ActionEnum,
        "Action to perform: STEP_INTO, STEP_OVER, STEP_OUT, RESUME, PAUSE, STOP, WAIT_FOR_PAUSE, DRAIN_EVENTS. "
        "Event draining is currently populated only by JVM-based debuggers (Java, Kotlin, etc.)."
    ],
    sessionId: Annotated[
        str | None,
        "Debug session ID. Use the current ID returned by `xdebug_get_debugger_status` or `xdebug_start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
        "If null and exactly one active session exists, it is selected automatically. "
        "If multiple sessions are active and sessionId is omitted, the call fails. Default: null."
    ] = None,
    timeout: Annotated[
        int,
        "Timeout in milliseconds to wait for action completion. "
        "Guidance: STEP_* / PAUSE usually 5000-15000; WAIT_FOR_PAUSE usually 30000-120000 depending on workload and breakpoints. "
        "Default: 30000."
    ] = 30000,
    eventsLimit: Annotated[
        int,
        "Maximum number of latest events to drain per event list. "
        "For DRAIN_EVENTS this limit is applied independently to breakpointErrorsTail and tracepointOutputsTail. "
        "Default: 100."
    ] = 100,
    clearEventsAfterRead: Annotated[
        bool | None,
        "Compatibility flag. Returned events are always removed from internal buffers, regardless of this value."
    ] = None,
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'status': {
    #       'type': 'string',
    #       'enum': [
    #         'running',
    #         'paused',
    #         'stopped'
    #       ],
    #       'description': 'Session state after the control action.'
    #     },
    #     'newPosition': {
    #       'type': [
    #         'object',
    #         'null'
    #       ],
    #       'required': [
    #         'filePath',
    #         'line'
    #       ],
    #       'properties': {
    #         'filePath': {
    #           'type': 'string',
    #           'description': 'File path as provided by the debugger (usually VirtualFile.url).'
    #         },
    #         'line': {
    #           'type': 'integer',
    #           'description': '1-based line number.'
    #         },
    #         'column': {
    #           'type': [
    #             'integer',
    #             'null'
    #           ],
    #           'description': '1-based column number when available.'
    #         }
    #       },
    #       'description': 'Current source position when the session is paused (if available).'
    #     },
    #     'frameValues': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Snapshot of current frame values when the session is paused, using the same text format as `xdebug_get_frame_values` with `depth=0`.'
    #     },
    #     'breakpointsMuted': {
    #       'type': 'boolean',
    #       'description': 'Whether breakpoints are globally muted for this debugger session.'
    #     },
    #     'message': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Additional context message for timeout/already-paused/already-stopped situations.'
    #     },
    #     'breakpointErrorsTail': {
    #       'type': [
    #         'array',
    #         'null'
    #       ],
    #       'items': {
    #         'type': 'object',
    #         'required': [
    #           'type',
    #           'timestampMs',
    #           'timestampIso',
    #           'sessionId',
    #           'message'
    #         ],
    #         'properties': {
    #           'type': {
    #             'type': 'string',
    #             'enum': [
    #               'BREAKPOINT_ERROR',
    #               'TRACEPOINT_OUTPUT'
    #             ],
    #             'description': 'Event type (BREAKPOINT_ERROR or TRACEPOINT_OUTPUT).'
    #           },
    #           'timestampMs': {
    #             'type': 'integer',
    #             'description': 'Unix timestamp in milliseconds when the event was recorded.'
    #           },
    #           'timestampIso': {
    #             'type': 'string',
    #             'description': 'ISO-8601 timestamp when the event was recorded.'
    #           },
    #           'sessionId': {
    #             'type': 'string',
    #             'description': 'Debugger session identifier.'
    #           },
    #           'message': {
    #             'type': 'string',
    #             'description': 'Primary event message.'
    #           },
    #           'breakpointId': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Canonical breakpoint ID when available.'
    #           },
    #           'filePath': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Breakpoint file path as provided by debugger when available.'
    #           },
    #           'line': {
    #             'type': [
    #               'integer',
    #               'null'
    #             ],
    #             'description': '1-based breakpoint line when available.'
    #           },
    #           'details': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Additional event context details when available.'
    #           }
    #         }
    #       },
    #       'description': 'Latest drained breakpoint error events. Returned for any control_session action. Indicates errors in breakpoints configuration like invalid conditional/log expressions. Currently populated only by JVM-based debuggers (Java, Kotlin, etc.).'
    #     },
    #     'tracepointOutputsTail': {
    #       'type': [
    #         'array',
    #         'null'
    #       ],
    #       'items': {
    #         'type': 'object',
    #         'required': [
    #           'type',
    #           'timestampMs',
    #           'timestampIso',
    #           'sessionId',
    #           'message'
    #         ],
    #         'properties': {
    #           'type': {
    #             'type': 'string',
    #             'enum': [
    #               'BREAKPOINT_ERROR',
    #               'TRACEPOINT_OUTPUT'
    #             ],
    #             'description': 'Event type (BREAKPOINT_ERROR or TRACEPOINT_OUTPUT).'
    #           },
    #           'timestampMs': {
    #             'type': 'integer',
    #             'description': 'Unix timestamp in milliseconds when the event was recorded.'
    #           },
    #           'timestampIso': {
    #             'type': 'string',
    #             'description': 'ISO-8601 timestamp when the event was recorded.'
    #           },
    #           'sessionId': {
    #             'type': 'string',
    #             'description': 'Debugger session identifier.'
    #           },
    #           'message': {
    #             'type': 'string',
    #             'description': 'Primary event message.'
    #           },
    #           'breakpointId': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Canonical breakpoint ID when available.'
    #           },
    #           'filePath': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Breakpoint file path as provided by debugger when available.'
    #           },
    #           'line': {
    #             'type': [
    #               'integer',
    #               'null'
    #             ],
    #             'description': '1-based breakpoint line when available.'
    #           },
    #           'details': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Additional event context details when available.'
    #           }
    #         }
    #       },
    #       'description': 'Latest drained tracepoint output events. Returned only for DRAIN_EVENTS action. Currently populated only by JVM-based debuggers (Java, Kotlin, etc.).'
    #     }
    #   },
    #   'required': [
    #     'status'
    #   ],
    #   'type': 'object'
    # }
    """Controls the execution of a debug session.
Use this tool to step through code, resume execution, pause, or stop the debug session.

Preconditions:
- A debug session must exist.
- `STEP_*` and `RESUME` require a suspended session.

Actions:
- STEP_INTO: Step into the next method call
- STEP_OVER: Step over the current line
- STEP_OUT: Step out of the current method
- RESUME: Resume program execution until the next breakpoint
- PAUSE: Pause program execution
- STOP: Stop the debug session
- WAIT_FOR_PAUSE: Wait until the session pauses (breakpoint hit or paused manually)
- DRAIN_EVENTS: Drain tracepoint outputs for the session (breakpoint errors are drained for all actions)

Important notes:
- If the program is running, use WAIT_FOR_PAUSE or PAUSE before STEP_* / RESUME.
- Use a current `sessionId` from `xdebug_get_debugger_status` or `xdebug_start_debugger_session`. If a session stops, times out, or disappears, refresh the session list before the next session-scoped call.
- RESUME does NOT set breakpoints. If there are no enabled breakpoints (or none will be hit next), the program may run to completion and the session may stop without pausing.
- After RESUME, call WAIT_FOR_PAUSE to confirm the next suspension. If WAIT_FOR_PAUSE times out, consider PAUSE and re-check breakpoints.
- `DRAIN_EVENTS` also requires an existing session; do not reuse a stale `sessionId` after the session has terminated.

Next call:
- After `RESUME`, call `xdebug_control_session(action=WAIT_FOR_PAUSE)`.
- After a paused result, call `xdebug_get_stack` / `xdebug_get_frame_values` / `xdebug_evaluate_expression`.

Status values in the result:
- running: Program is executing
- paused: Execution is suspended (breakpoint, step, or manual pause); paused results also include `frameValues`, a current-frame snapshot in `xdebug_get_frame_values(depth=0)` format when available
- stopped: Debug session has terminated
- `breakpointErrorsTail` is returned for any action
- `tracepointOutputsTail` is returned only for `DRAIN_EVENTS`

Event support scope:
- Breakpoint error and tracepoint output events are currently reported only by JVM-based debuggers (Java, Kotlin, etc.).
- On other debugger backends these event tails can be empty even when breakpoints/logging are configured."""
    print(action)
    print(sessionId)
    print(timeout)
    print(eventsLimit)
    print(clearEventsAfterRead)
    print(projectPath)
