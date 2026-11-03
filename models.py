from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field

from enums import SessionState, ThreadState
from utils import fetch_line_text


class Breakpoint(BaseModel):
    """A configured breakpoint."""

    # `id` is excluded because it's unstable. All IDs change anytime we mute/unmute all breakpoints, for example
    id: Annotated[int | None, Field(description="Breakpoint id.", exclude=True)]
    file: Annotated[Path, Field(default=None, description="File path of the breakpoint.")]
    line: Annotated[int, Field(default=None, description="1-based breakpoint line number.")]
    line_text: Annotated[
        str | None,
        Field(
            default=None,
            description="Short excerpt of the actual source line where the breakpoint resides, truncated when needed. Present for line breakpoints only.",
            exclude_if=lambda v: v is None,
        ),
    ] = None
    condition: Annotated[
        str | None,
        Field(
            default=None,
            description="Conditional expression for triggering breakpoint, if set.",
            exclude_if=lambda v: v is None,
        ),
    ] = None
    temporary: Annotated[bool, Field(description="Whether breakpoint is temporary.")]
    hit_count: Annotated[int, Field(description="Breakpoint hit count, 0 when unavailable.")]

    def to_dap(self) -> dict[str, Any]:
        """Turn this breakpoint into a dictionary that can be sent to DAP. Matches the "SourceBreakpoint" DAP schema."""
        return {"line": self.line, "condition": self.condition}

    @classmethod
    def floating(cls, path: Path, line: int) -> Breakpoint:
        """
        Create a floating breakpoint, on the given line of a given file.
        This happens when hitting the hard pause button, or stepping over/into/out of methods.
        It's equivalent to the "you are here" indicator in a traditional debugger UI.
        """
        return cls(
            id=None,
            file=path,
            line=line,
            line_text=fetch_line_text(path, line),
            condition=None,
            temporary=True,
            hit_count=1,
        )


class BreakpointsResponse(BaseModel):
    """List of configured breakpoints."""

    breakpoints: Annotated[list[Breakpoint], Field(description="List of currently configured breakpoints.")]
    breakpoints_muted: Annotated[
        bool,
        Field(default=False, description="Whether breakpoints are globally muted for the resolved debugger session."),
    ]


class SessionStatus(BaseModel):
    """Status of a debug session."""

    id: Annotated[str, Field(description="Session identifier to use as `session_id` in subsequent debugger calls.")]
    state: Annotated[SessionState, Field(description="Current session state.")]
    debugee_pid: Annotated[
        int | None,
        Field(
            description="Pid of the process being debugged, if this MCP server knows it.",
            exclude_if=lambda v: v is None,
        ),
    ] = None
    std_out_path: Annotated[
        str | None,
        Field(
            default=None,
            description="Path to a temp file where the debugee process puts its stdout. The file will continue growing while the process is still running and remains available after session termination.",
            exclude_if=lambda v: v is None,
        ),
    ] = None
    std_err_path: Annotated[
        str | None,
        Field(
            default=None,
            description="Path to a temp file where the debugee process puts its stdout. The file will continue growing while the process is still running and remains available after session termination.",
            exclude_if=lambda v: v is None,
        ),
    ] = None
    breakpoints_muted: Annotated[
        bool, Field(default=False, description="Whether breakpoints are globally muted for this debugger session."),
    ]
    current_position: Annotated[
        Breakpoint | None,
        Field(default=None, description="Current source position for paused sessions, if available."),
    ] = None


class SessionStatuses(BaseModel):
    """Statuses of all active debug sessions."""

    sessions: Annotated[list[SessionStatus], Field(description="All currently known debug sessions.")]


class StackFrame(BaseModel):
    """A stack frame."""

    id: Annotated[int, Field(description="Stack frame id.")]
    name: Annotated[
        str | None,
        Field(
            description="Name of the stack frame. Usually the function name, or <module> for lines outside a function.",
        ),
    ] = None
    file: Annotated[
        str | None, Field(default=None, description="Source file path as provided by the debugger when available."),
    ] = None
    line: Annotated[int | None, Field(default=None, description="1-based source line when available.")] = None
    library_code: Annotated[bool, Field(description="Whether this stack frame appears to be from library code or not.")]

    @classmethod
    def from_dap(cls, dap_frame: dict[str, Any]) -> StackFrame:
        return cls(
            id=dap_frame["id"],
            name=dap_frame.get("name"),
            file=dap_frame.get("source", {}).get("path"),
            line=dap_frame.get("line"),
            library_code=True if dap_frame.get("presentationHint") == "subtle" else False,
        )


class StackFrames(BaseModel):
    """Call stack for a debugged thread."""

    frames: Annotated[
        list[StackFrame],
        Field(description="Stack frames for the selected thread, ordered from top (index 0) to older frames."),
    ]
    thread_id: Annotated[int, Field(description="Thread identifier used to fetch this stack.")]
    total_frames: Annotated[int, Field(description="Total frame count for the stack.")]


class Thread(BaseModel):
    """A thread in the debug session."""

    id: Annotated[int, Field(description="Thread identifier to pass as `thread_id` in `get_stack`.")]
    name: Annotated[str | None, Field(description="Human-readable thread name.")]
    state: Annotated[ThreadState, Field(description="Current thread status as last reported to the debugger.")]
    is_current: Annotated[bool, Field(description="Whether this thread is currently selected.")]


class ThreadsResponse(BaseModel):
    """List of threads in the debug session."""

    threads: Annotated[list[Thread], Field(description="Threads available in the suspended debug session (paginated).")]
    total_count: Annotated[int, Field(description="Total known thread count.")]


class Variable(BaseModel):
    """A variable."""
    id: Annotated[int, Field(description="Variable id. Very often 0, if the variable has no children.", exclude=True)]
    name: Annotated[str, Field(description="Name of the variable.")]
    value: Annotated[str, Field(description="Current value of the variable.")]
    type: Annotated[str, Field(description="Type of the variable.")]
    evaluate_name: Annotated[
        str | None,
        Field(description="Name of the variable if you want to evaluate it.", exclude_if=lambda v: v is None),
    ] = None
    presentation_hint: Annotated[Any, Field(description="Presentation hint.", exclude_if=lambda v: not v)]
    children: Annotated[list[Variable] | None, Field(description="Children of this variable.")]

    @classmethod
    def from_dap_variable(cls, dap_variable: dict[str, Any]) -> Variable:
        variable_id = dap_variable["variablesReference"]
        variable_type = dap_variable["type"]
        # This is a python specific quirk, we get variables with evaluation names that don't actually work
        # Every single one I've seen has "type": "", so to not mislead the LLM, we remove those bad eval names
        evaluate_name = dap_variable.get("evaluateName") if variable_type else None
        return cls(
            id=variable_id,
            name=dap_variable["name"],
            value=dap_variable["value"],
            type=variable_type,
            evaluate_name=evaluate_name,
            presentation_hint=dap_variable.get("presentationHint"),
            children=None if variable_id == 0 else [],
        )

    @classmethod
    def from_dap_evaluation(cls, dap_evaluation: dict[str, Any], evaluate_name: str) -> Variable:
        variable_id = dap_evaluation["variablesReference"]
        return cls(
            id=variable_id,
            name=evaluate_name,
            value=dap_evaluation["result"],
            type=dap_evaluation["type"],
            evaluate_name=evaluate_name,
            presentation_hint=dap_evaluation.get("presentationHint"),
            children=None if variable_id == 0 else [],
        )


class Variables(BaseModel):
    """A list of variables."""
    variables: Annotated[list[Variable], Field(description="A list of variables.")]
