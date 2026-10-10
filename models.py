from typing import Annotated

from pydantic import BaseModel, Field

from enums import BreakpointOwner, DebuggerEventType, DebuggerOutcome, DebuggerState


class Breakpoint(BaseModel):
    """A configured breakpoint."""

    id: Annotated[str, Field(description="Canonical breakpoint ID (stable across list/remove).")]
    type: Annotated[str, Field(description="Breakpoint type (line/exception/other).")]
    file: Annotated[
        str | None,
        Field(default=None, description="File path of the breakpoint as provided by the debugger (usually file URL)."),
    ] = None
    line: Annotated[int | None, Field(default=None, description="1-based breakpoint line when available.")] = None
    enabled: Annotated[bool, Field(description="Whether breakpoint is enabled.")]
    owner: Annotated[
        BreakpointOwner,
        Field(description="Breakpoint ownership marker: `agent` if created/updated by MCP toolset, otherwise `user`."),
    ]
    condition: Annotated[
        str | None, Field(default=None, description="Conditional expression for triggering breakpoint, if set."),
    ] = None
    log_expression: Annotated[
        str | None,
        Field(
            default=None,
            description="Evaluate-and-log expression of the logpoint, if set (the value logged when the line is reached).",
        ),
    ] = None
    is_log_message: Annotated[bool, Field(description="Whether breakpoint logs source position when hit.")]
    is_log_stack: Annotated[bool, Field(description="Whether breakpoint logs stack trace when hit.")]
    temporary: Annotated[bool, Field(description="Whether breakpoint is temporary.")]
    suspend_policy: Annotated[str, Field(description="Breakpoint suspend policy (all/thread/none).")]
    hit_count: Annotated[int, Field(description="Breakpoint hit count, 0 when unavailable.")]


class DebuggerEvent(BaseModel):
    """A debugger event."""

    type: Annotated[DebuggerEventType, Field(description="Event type (BREAKPOINT_ERROR or TRACEPOINT_OUTPUT).")]
    timestamp_ms: Annotated[int, Field(description="Unix timestamp in milliseconds when the event was recorded.")]
    # TODO: try having this be a native datetime, see if it marshalls
    timestamp_iso: Annotated[str, Field(description="ISO-8601 timestamp when the event was recorded.")]
    session_id: Annotated[str, Field(description="Debugger session identifier.")]
    message: Annotated[str, Field(description="Primary event message.")]
    breakpoint_id: Annotated[
        str | None, Field(default=None, description="Canonical breakpoint ID when available."),
    ] = None
    file_path: Annotated[
        str | None, Field(default=None, description="Breakpoint file path as provided by debugger when available."),
    ] = None
    line: Annotated[int | None, Field(default=None, description="1-based breakpoint line when available.")] = None
    details: Annotated[
        str | None, Field(default=None, description="Additional event context details when available."),
    ] = None


class SourcePosition(BaseModel):
    """An absolute position in source code."""

    file_path: Annotated[str, Field(description="File path as provided by the debugger (usually VirtualFile.url).")]
    line: Annotated[int, Field(description="1-based line number.")]
    column: Annotated[int | None, Field(default=None, description="1-based column number when available.")] = None


class SessionStatus(BaseModel):
    """Status of a debug session."""

    id: Annotated[str, Field(description="Session identifier to use as `session_id` in subsequent debugger calls.")]
    state: Annotated[DebuggerState, Field(description="Current session state.")]
    debugee_pid: Annotated[int | None, "Pid of the process being debugged, if this MCP server knows it."]
    std_out_path: Annotated[
        str | None,
        Field(
            default=None,
            description="Path to a temp file where the debugee process puts its stdout. The file will continue growing while the process is still running and remains available after session termination.",
        ),
    ] = None
    std_err_path: Annotated[
        str | None,
        Field(
            default=None,
            description="Path to a temp file where the debugee process puts its stdout. The file will continue growing while the process is still running and remains available after session termination.",
        ),
    ] = None
    breakpoints_muted: Annotated[
        bool, Field(default=False, description="Whether breakpoints are globally muted for this debugger session."),
    ]
    current_position: Annotated[
        SourcePosition | None,
        Field(default=None, description="Current source position for paused sessions, if available."),
    ] = None


class SessionStatuses(BaseModel):
    """Statuses of all active debug sessions."""

    sessions: Annotated[list[SessionStatus], Field(description="All currently known debug sessions.")]


class StackFrame(BaseModel):
    """A stack frame."""

    presentation: Annotated[str, Field(description="Rendered function/method frame label from debugger UI.")]
    index: Annotated[int, Field(description="0-based frame index to use as `frame_index` in other debugger tools.")]
    file: Annotated[
        str | None, Field(default=None, description="Source file path as provided by the debugger when available."),
    ] = None
    line: Annotated[int | None, Field(default=None, description="1-based source line when available.")] = None
    is_current: Annotated[bool, Field(description="Whether this is the currently selected frame.")]


class Thread(BaseModel):
    """A thread in the debug session."""

    id: Annotated[int, Field(description="Thread identifier to pass as `thread_id` in `get_stack`.")]
    name: Annotated[str, Field(description="Human-readable thread name.")]
    # state: Annotated[str, Field(description="Current thread status from debugger perspective.")]
    # is_current: Annotated[bool, Field(description="Whether this thread is currently selected.")]
    # additional_info: Annotated[
    #     str | None, Field(default=None, description="Additional thread display info when available."),
    # ] = None
    # additional_info_tooltip: Annotated[
    #     str | None, Field(default=None, description="Tooltip for additional thread display info when available."),
    # ] = None
    # frame_count: Annotated[int | None, Field(default=None, description="Number of stack frames when available.")] = None


class StackResponse(BaseModel):
    """Call stack for a debugged thread."""

    frames: Annotated[
        list[StackFrame],
        Field(description="Stack frames for the selected thread, ordered from top (index 0) to older frames."),
    ]
    thread_id: Annotated[
        int | None, Field(default=None, description="Thread identifier used to fetch this stack."),
    ] = None
    total_frames: Annotated[int, Field(description="Total frame count for the stack.")]


class ThreadsResponse(BaseModel):
    """List of threads in the debug session."""

    threads: Annotated[list[Thread], Field(description="Threads available in the suspended debug session (paginated).")]
    total_count: Annotated[int, Field(description="Total known thread count.")]


class BreakpointsResponse(BaseModel):
    """List of configured breakpoints."""

    breakpoints: Annotated[list[Breakpoint], Field(description="List of currently configured breakpoints.")]
    total_count: Annotated[int, Field(description="Total count.")]
    enabled_count: Annotated[int, Field(description="Enabled count.")]
    breakpoints_muted: Annotated[
        bool,
        Field(default=False, description="Whether breakpoints are globally muted for the resolved debugger session."),
    ]


class RemoveBreakpointResponse(BaseModel):
    """Result of a breakpoint removal operation."""

    removed: Annotated[bool, Field(description="Whether at least one breakpoint was removed.")]
    removed_count: Annotated[int, Field(description="Number of breakpoints removed at the requested location.")]
    breakpoint_id: Annotated[
        str | None, Field(default=None, description="Removed breakpoint ID when operation targeted one ID."),
    ] = None
    total_breakpoints: Annotated[int, Field(description="Current total number of breakpoints after removal.")]
    message: Annotated[
        str | None, Field(default=None, description="Additional note when no matching breakpoint is found."),
    ] = None


class RunToLineResponse(BaseModel):
    """Result of a run-to-line operation."""

    session_id: Annotated[str, Field(description="Session identifier.")]
    outcome: Annotated[
        DebuggerOutcome, Field(description="Outcome after attempting run-to-line (paused/stopped/timeout)."),
    ]
    current_position: Annotated[
        SourcePosition | None,
        Field(default=None, description="Current position when outcome is paused and position is known."),
    ] = None
    message: Annotated[
        str | None, Field(default=None, description="Additional context message (timeout or errors)."),
    ] = None


class SetBreakpointResponse(BaseModel):
    """Result of a breakpoint set/update operation."""

    breakpoint_id: Annotated[
        str | None,
        Field(default=None, description="Canonical breakpoint ID. Absent for breakpoint mute-only operations."),
    ] = None
    previous_breakpoint_id: Annotated[
        str | None,
        Field(
            default=None,
            description="Previous canonical breakpoint ID when operation relocated an existing line breakpoint.",
        ),
    ] = None
    added: Annotated[
        Breakpoint | None,
        Field(
            default=None,
            description="Details of the newly added or updated breakpoint. Absent for breakpoint mute-only operations.",
        ),
    ] = None
    total_breakpoints: Annotated[int, Field(description="Current total number of breakpoints after operation.")]
    line_text: Annotated[
        str | None,
        Field(
            default=None,
            description="Short excerpt of the actual source line where the breakpoint resides, truncated when needed. Present for line breakpoints only.",
        ),
    ] = None
    breakpoints_muted: Annotated[
        bool,
        Field(default=False, description="Whether breakpoints are globally muted for the resolved debugger session."),
    ]
    message: Annotated[
        str | None, Field(default=None, description="Additional note when requested and actual positions differ."),
    ] = None


class SetVariableResponse(BaseModel):
    """Response from mutating a variable value by path in the selected stack frame."""

    path: Annotated[list[str], Field(description="Variable path used for mutation.")]
    old_value: Annotated[str, Field(description="Value before mutation.")]
    new_value: Annotated[str, Field(description="Value after mutation.")]
    applied: Annotated[bool, Field(description="Whether mutation was applied.")]
