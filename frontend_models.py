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
    logExpression: Annotated[
        str | None,
        Field(
            default=None,
            description="Evaluate-and-log expression of the logpoint, if set (the value logged when the line is reached).",
        ),
    ] = None
    isLogMessage: Annotated[bool, Field(description="Whether breakpoint logs source position when hit.")]
    isLogStack: Annotated[bool, Field(description="Whether breakpoint logs stack trace when hit.")]
    temporary: Annotated[bool, Field(description="Whether breakpoint is temporary.")]
    suspendPolicy: Annotated[str, Field(description="Breakpoint suspend policy (all/thread/none).")]
    hitCount: Annotated[int, Field(description="Breakpoint hit count, 0 when unavailable.")]


class DebuggerEvent(BaseModel):
    """A debugger event."""

    type: Annotated[DebuggerEventType, Field(description="Event type (BREAKPOINT_ERROR or TRACEPOINT_OUTPUT).")]
    timestampMs: Annotated[int, Field(description="Unix timestamp in milliseconds when the event was recorded.")]
    # TODO: try having this be a native datetime, see if it marshalls
    timestampIso: Annotated[str, Field(description="ISO-8601 timestamp when the event was recorded.")]
    sessionId: Annotated[str, Field(description="Debugger session identifier.")]
    message: Annotated[str, Field(description="Primary event message.")]
    breakpointId: Annotated[
        str | None, Field(default=None, description="Canonical breakpoint ID when available."),
    ] = None
    filePath: Annotated[
        str | None, Field(default=None, description="Breakpoint file path as provided by debugger when available."),
    ] = None
    line: Annotated[int | None, Field(default=None, description="1-based breakpoint line when available.")] = None
    details: Annotated[
        str | None, Field(default=None, description="Additional event context details when available."),
    ] = None


class SourcePosition(BaseModel):
    """An absolute position in source code."""

    filePath: Annotated[str, Field(description="File path as provided by the debugger (usually VirtualFile.url).")]
    line: Annotated[int, Field(description="1-based line number.")]
    column: Annotated[int | None, Field(default=None, description="1-based column number when available.")] = None


class DebugSession(BaseModel):
    """A debug session."""

    id: Annotated[
        str,
        Field(
            description="Session identifier to use as `sessionId` in debugger calls. Uses session name by default; if duplicate names exist, format is `<sessionName>#<executionId>`.",
        ),
    ]
    name: Annotated[str, Field(description="Session display name.")]
    state: Annotated[DebuggerState, Field(description="Current session state.")]
    runConfigurationName: Annotated[
        str | None, Field(default=None, description="Associated run configuration name when available."),
    ] = None
    breakpointsMuted: Annotated[
        bool, Field(default=False, description="Whether breakpoints are globally muted for this debugger session."),
    ]
    currentPosition: Annotated[
        SourcePosition | None,
        Field(default=None, description="Current source position for paused sessions, if available."),
    ] = None


class StackFrame(BaseModel):
    """A stack frame."""

    presentation: Annotated[str, Field(description="Rendered function/method frame label from debugger UI.")]
    index: Annotated[int, Field(description="0-based frame index to use as `frameIndex` in other debugger tools.")]
    file: Annotated[
        str | None, Field(default=None, description="Source file path as provided by the debugger when available."),
    ] = None
    line: Annotated[int | None, Field(default=None, description="1-based source line when available.")] = None
    isCurrent: Annotated[bool, Field(description="Whether this is the currently selected frame.")]


class Thread(BaseModel):
    """A thread in the debug session."""

    id: Annotated[str, Field(description="Thread identifier to pass as `threadId` in `get_stack`.")]
    name: Annotated[str, Field(description="Human-readable thread name.")]
    state: Annotated[str, Field(description="Current thread status from debugger perspective.")]
    isCurrent: Annotated[bool, Field(description="Whether this thread is currently selected.")]
    additionalInfo: Annotated[
        str | None, Field(default=None, description="Additional thread display info when available."),
    ] = None
    additionalInfoTooltip: Annotated[
        str | None, Field(default=None, description="Tooltip for additional thread display info when available."),
    ] = None
    frameCount: Annotated[int | None, Field(default=None, description="Number of stack frames when available.")] = None


class ControlSessionResponse(BaseModel):
    """Response from a debug session control action."""

    status: Annotated[DebuggerState, Field(description="Session state after the control action.")]
    newPosition: Annotated[
        SourcePosition | None,
        Field(default=None, description="Current source position when the session is paused (if available)."),
    ] = None
    frameValues: Annotated[
        str | None,
        Field(
            default=None,
            description="Snapshot of current frame values when the session is paused, using the same text format as `get_frame_values` with `depth=0`.",
        ),
    ] = None
    breakpointsMuted: Annotated[
        bool,
        Field(default=False, description="Whether breakpoints are globally muted for this debugger session."),
    ]
    message: Annotated[
        str | None,
        Field(
            default=None,
            description="Additional context message for timeout/already-paused/already-stopped situations.",
        ),
    ] = None
    breakpointErrorsTail: Annotated[
        list[DebuggerEvent] | None,
        Field(
            default=None,
            description="Latest drained breakpoint error events. Returned for any control_session action. Indicates errors in breakpoints configuration like invalid conditional/log expressions. Currently populated only by JVM-based debuggers (Java, Kotlin, etc.).",
        ),
    ] = None
    tracepointOutputsTail: Annotated[
        list[DebuggerEvent] | None,
        Field(
            default=None,
            description="Latest drained tracepoint output events. Returned only for DRAIN_EVENTS action. Currently populated only by JVM-based debuggers (Java, Kotlin, etc.).",
        ),
    ] = None


class DebuggerStatusResponse(BaseModel):
    """Current debugger status with all active sessions."""

    sessions: Annotated[list[DebugSession], Field(description="All currently known debug sessions.")]
    activeSessionId: Annotated[
        str | None, Field(default=None, description="Identifier of the active session, if any."),
    ] = None


class StackResponse(BaseModel):
    """Call stack for a debugged thread."""

    frames: Annotated[
        list[StackFrame],
        Field(description="Stack frames for the selected thread, ordered from top (index 0) to older frames."),
    ]
    threadId: Annotated[
        str | None, Field(default=None, description="Thread identifier used to fetch this stack."),
    ] = None
    totalFrames: Annotated[int, Field(description="Total frame count for the stack.")]


class ThreadsResponse(BaseModel):
    """List of threads in the debug session."""

    threads: Annotated[list[Thread], Field(description="Threads available in the suspended debug session (paginated).")]
    offset: Annotated[int, Field(description="Requested page offset.")]
    limit: Annotated[int, Field(description="Requested page limit.")]
    totalCount: Annotated[int, Field(description="Total known thread count.")]


class BreakpointsResponse(BaseModel):
    """List of configured breakpoints."""

    breakpoints: Annotated[list[Breakpoint], Field(description="List of currently configured breakpoints.")]
    totalCount: Annotated[int, Field(description="Total count.")]
    enabledCount: Annotated[int, Field(description="Enabled count.")]
    breakpointsMuted: Annotated[
        bool,
        Field(default=False, description="Whether breakpoints are globally muted for the resolved debugger session."),
    ]


class RemoveBreakpointResponse(BaseModel):
    """Result of a breakpoint removal operation."""

    removed: Annotated[bool, Field(description="Whether at least one breakpoint was removed.")]
    removedCount: Annotated[int, Field(description="Number of breakpoints removed at the requested location.")]
    breakpointId: Annotated[
        str | None, Field(default=None, description="Removed breakpoint ID when operation targeted one ID."),
    ] = None
    totalBreakpoints: Annotated[int, Field(description="Current total number of breakpoints after removal.")]
    message: Annotated[
        str | None, Field(default=None, description="Additional note when no matching breakpoint is found."),
    ] = None


class RunToLineResponse(BaseModel):
    """Result of a run-to-line operation."""

    sessionId: Annotated[str, Field(description="Session identifier.")]
    outcome: Annotated[
        DebuggerOutcome, Field(description="Outcome after attempting run-to-line (paused/stopped/timeout)."),
    ]
    currentPosition: Annotated[
        SourcePosition | None,
        Field(default=None, description="Current position when outcome is paused and position is known."),
    ] = None
    message: Annotated[
        str | None, Field(default=None, description="Additional context message (timeout or errors)."),
    ] = None


class SetBreakpointResponse(BaseModel):
    """Result of a breakpoint set/update operation."""

    breakpointId: Annotated[
        str | None,
        Field(default=None, description="Canonical breakpoint ID. Absent for breakpoint mute-only operations."),
    ] = None
    previousBreakpointId: Annotated[
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
    totalBreakpoints: Annotated[int, Field(description="Current total number of breakpoints after operation.")]
    lineText: Annotated[
        str | None,
        Field(
            default=None,
            description="Short excerpt of the actual source line where the breakpoint resides, truncated when needed. Present for line breakpoints only.",
        ),
    ] = None
    breakpointsMuted: Annotated[
        bool,
        Field(default=False, description="Whether breakpoints are globally muted for the resolved debugger session."),
    ]
    message: Annotated[
        str | None, Field(default=None, description="Additional note when requested and actual positions differ."),
    ] = None


class SetVariableResponse(BaseModel):
    """Response from mutating a variable value by path in the selected stack frame."""

    path: Annotated[list[str], Field(description="Variable path used for mutation.")]
    oldValue: Annotated[str, Field(description="Value before mutation.")]
    newValue: Annotated[str, Field(description="Value after mutation.")]
    applied: Annotated[bool, Field(description="Whether mutation was applied.")]


class StartDebuggerSessionResponse(BaseModel):
    """Response from starting a debugger session for a run configuration or code location."""

    sessionId: Annotated[
        str,
        Field(
            description="Session identifier to use as `sessionId` in subsequent debugger calls. Uses session name by default; if duplicate names exist, format is `<sessionName>#<executionId>`.",
        ),
    ]
    name: Annotated[str, Field(description="Human-readable session name.")]
    state: Annotated[DebuggerState, Field(description="Current session state.")]
    runConfigurationName: Annotated[
        str | None, Field(default=None, description="Associated run configuration name, if available."),
    ] = None
    # TODO: not sure if this is optional or not
    breakpointsMuted: Annotated[
        bool,
        Field(default=False, description="Whether breakpoints are globally muted for this debugger session."),
    ]
    exitCode: Annotated[
        int | None,
        Field(
            default=None,
            description="Process exit code. Absent when the tool returns before observing process termination, for example when the debuggee continues running after the session starts.",
        ),
    ] = None
    output: Annotated[
        str,
        Field(
            description="Captured process output snapshot. When additional output exists, `<truncated>` is appended to the preview.",
        ),
    ]
    fullOutputPath: Annotated[
        str | None,
        Field(
            default=None,
            description="Path to a temp file containing the full raw output. The file may continue growing while the process is still running and remains available while the IDE is running.",
        ),
    ] = None
