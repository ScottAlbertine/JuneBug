from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field

from enums import BreakpointType, DebuggerOutcome, DebuggerState, SuspendPolicy, ThreadState


class Breakpoint(BaseModel):
    """A configured breakpoint."""

    type: Annotated[BreakpointType, Field(description="Breakpoint type (line/exception/other).")]
    file: Annotated[Path, Field(default=None, description="File path of the breakpoint.")]
    line: Annotated[int, Field(default=None, description="1-based breakpoint line number.")]
    line_text: Annotated[
        str | None,
        Field(
            default=None,
            description="Short excerpt of the actual source line where the breakpoint resides, truncated when needed. Present for line breakpoints only.",
        ),
    ] = None
    condition: Annotated[
        str | None, Field(default=None, description="Conditional expression for triggering breakpoint, if set."),
    ] = None
    temporary: Annotated[bool, Field(description="Whether breakpoint is temporary.")]
    suspend_policy: Annotated[SuspendPolicy, Field(description="Breakpoint suspend policy (all/thread/none).")]
    hit_count: Annotated[int, Field(description="Breakpoint hit count, 0 when unavailable.")]

    def to_dap(self) -> dict[str, Any]:
        """Turn this breakpoint into a dictionary that can be sent to DAP. Matches the "SourceBreakpoint" DAP schema."""
        return {"line": self.line, "condition": self.condition}


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
    name: Annotated[str | None, Field(description="Human-readable thread name.")]
    state: Annotated[ThreadState, Field(description="Current thread status as last reported to the debugger.")]
    is_current: Annotated[bool, Field(description="Whether this thread is currently selected.")]


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


class SetVariableResponse(BaseModel):
    """Response from mutating a variable value by path in the selected stack frame."""

    path: Annotated[list[str], Field(description="Variable path used for mutation.")]
    old_value: Annotated[str, Field(description="Value before mutation.")]
    new_value: Annotated[str, Field(description="Value after mutation.")]
    applied: Annotated[bool, Field(description="Whether mutation was applied.")]
