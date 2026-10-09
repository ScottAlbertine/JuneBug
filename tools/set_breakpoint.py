from typing import Annotated

from annotations import ProjectPath
from enums import SuspendPolicy
from frontend_models import SetBreakpointResponse


def set_breakpoint(
    project_path: ProjectPath,
    breakpoint_id: Annotated[
        str | None,
        "Canonical breakpoint ID returned by `set_breakpoint` or `list_breakpoints`. "
        "If provided, the tool runs in ID mode. "
        "Omit this or pass null in location mode; do not use placeholder strings such as empty string or fake path-like values. "
        "Default: null.",
    ] = None,
    session_id: Annotated[
        str | None,
        "Debug session ID. Use the current ID returned by `get_debugger_status` or `start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
        "If null and exactly one active session exists, it is selected automatically. "
        "If multiple sessions are active and session_id is omitted, the call fails. "
        "Default: null. "
        "Use with `breakpoints_muted` in a dedicated mute-only call; do not combine that call with breakpoint target or settings parameters.",
    ] = None,
    file_path: Annotated[
        str | None,
        "Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, archive entries like '/path/lib.jar!/pkg/Foo.class', "
        "and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools). "
        "Required only in location mode. Optional in ID mode to relocate line breakpoints.",
    ] = None,
    line: Annotated[
        int | None,
        "1-based line number. Required only in location mode. Optional in ID mode to relocate line breakpoints.",
    ] = None,
    condition: Annotated[
        str | None,
        "Optional condition expression - breakpoint will only trigger when this evaluates to true. "
        "Validation errors are reported asynchronously via control_session(...).breakpoint_errors_tail (JVM-based debuggers only). "
        "Default: null.",
    ] = None,
    log_expression: Annotated[
        str | None,
        "The Evaluate-and-log expression. "
        "When set, its result is logged each time the breakpoint is hit, read via control_session(action=DRAIN_EVENTS).tracepoint_outputs_tail. "
        "Combine with suspend_policy=NONE to make a non-suspending logpoint - the preferred, most important way to capture runtime values without freezing threads. "
        "Keep it side-effect-free (no mutation, I/O, or iterator/stream advancement). log_expression=null clears it. "
        "Default: null.",
    ] = None,
    is_log_message: Annotated[
        bool,
        "Whether to log breakpoint hit position (source location) when breakpoint is reached. "
        "In JVM-based debuggers output is available via control_session(action=DRAIN_EVENTS).tracepoint_outputs_tail. "
        "Default: false.",
    ] = False,
    is_log_stack: Annotated[
        bool,
        "Whether to log stack trace when breakpoint is reached. "
        "In JVM-based debuggers output is available via control_session(action=DRAIN_EVENTS).tracepoint_outputs_tail. "
        "Default: false.",
    ] = False,
    temporary: Annotated[bool, "Temporary breakpoint (removed after first hit). Default: false."] = False,
    suspend_policy: Annotated[SuspendPolicy, "Suspend policy: ALL, THREAD, NONE. Default: ALL."] = SuspendPolicy.ALL,
    enabled: Annotated[bool, "Whether breakpoint is enabled. Default: true."] = True,
    breakpoints_muted: Annotated[
        bool | None,
        "Session-wide breakpoint mute flag. "
        "When provided, call this tool with only `session_id` plus `breakpoints_muted`; "
        "do not pass breakpoint_id, file_path, line, condition, logging, suspend, temporary, or enabled parameters. "
        "Default: null.",
    ] = None,
) -> SetBreakpointResponse:
    """Creates or updates a breakpoint or a logpoint (a non-suspending "Evaluate and log" breakpoint).
Use this tool to set line breakpoints, set logpoints via `log_expression`, update existing breakpoints by ID, and control tracepoint/logging behavior.

Logpoints are the preferred, low-disturbance probe, and providing a `log_expression` is the most important input:
set `log_expression` together with `suspend_policy=NONE` to evaluate an expression and log its result every time the line
is reached WITHOUT stopping execution — the primary way to capture runtime values, branch/reachability evidence, counts,
and identifiers. Read the logged output via `control_session(action=DRAIN_EVENTS).tracepoint_outputs_tail`.

Targeting modes:
- By location: provide `file_path` + `line`, and omit `breakpoint_id` (or pass null). Do not use placeholder strings such as `""`, `"/"`, or `"__omit__"`.
- By ID: provide an existing opaque canonical `breakpoint_id` returned by `set_breakpoint` or `list_breakpoints` (optional `file_path`/`line` can relocate line breakpoints).
- Breakpoint mute-only: provide only `session_id` and `breakpoints_muted`.
  Do not combine `breakpoints_muted` with breakpoint target or settings parameters.

Validation:
- In location mode, both `file_path` and `line` are required.
- In ID mode, breakpoint must exist and be uniquely identified by `breakpoint_id`.
- In location mode, `file_path` is relative to the project root, `line` is 1-based, and the target location must be executable.
- In breakpoint mute-only mode, a debugger session must be resolved from `session_id` or the single active session.

Event reporting:
- Invalid `condition` expressions are reported asynchronously via `control_session(...).breakpoint_errors_tail`.
- Tracepoint output from breakpoints with `is_log_message` and/or `is_log_stack` is drained via `control_session(action=DRAIN_EVENTS).tracepoint_outputs_tail`.
- Breakpoint-error and tracepoint-output reporting is currently supported only by JVM-based debuggers (Java, Kotlin, etc.).
- A successful `set_breakpoint` response does not guarantee that `condition` or tracepoint expressions are valid; check later `breakpoint_errors_tail` before relying on them.
- Successful line-breakpoint responses also include `line_text`, a truncated excerpt of the actual source line where the breakpoint now resides. Inspect it to confirm placement before resuming.

Apply semantics:
- Provided fields are applied as the resulting state for the target breakpoint.
- `condition=null` clears existing condition.
- `log_expression` sets the Evaluate-and-log expression that is evaluated and logged when the breakpoint is hit; `log_expression=null` clears it. Combine with `suspend_policy=NONE` for a non-suspending logpoint (the preferred way to capture values). Keep it side-effect-free; evaluation errors surface in `breakpoint_errors_tail`.
- `is_log_message=true` logs breakpoint hit position.
- `is_log_stack=true` logs current stack trace.
- If both flags are true, both position and stack are logged.
- With `is_log_message`/`is_log_stack` + `suspend_policy=NONE`, the breakpoint behaves as a tracepoint.
- In ID mode, if `file_path`/`line` are provided for a line breakpoint, it is relocated (recreated) at the new location.
- In ID mode, for non-line breakpoints, `file_path`/`line` are ignored and reported in `message`.
- `breakpoints_muted` is a session-wide debugger flag; use it in a dedicated call with only `session_id` and `breakpoints_muted`.
  It does not change the per-breakpoint `enabled` value.
- Any successful operation marks breakpoint as `agent` ownership (`mcpBreakpointMarker`).

Next call:
- Use returned `line_text` and/or `list_breakpoints` to verify placement.
- Start/continue execution via `start_debugger_session` or `control_session(action=RESUME)`."""
    print(breakpoint_id)
    print(session_id)
    print(file_path)
    print(line)
    print(condition)
    print(log_expression)
    print(is_log_message)
    print(is_log_stack)
    print(temporary)
    print(suspend_policy)
    print(enabled)
    print(breakpoints_muted)
    print(project_path)
