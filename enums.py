from enum import Enum


class Action(Enum):
    STEP_INTO = "step_into"
    STEP_OVER = "step_over"
    STEP_OUT = "step_out"
    RESUME = "resume"
    PAUSE = "pause"
    STOP = "stop"
    WAIT_FOR_PAUSE = "wait_for_pause"


class ExceptionBreakpointMode(Enum):
    RAISED = "raised"
    UNHANDLED = "unhandled"
    USER_UNHANDLED = "user_unhandled"

    def to_dap_break_mode(self) -> str:
        """Convert to a DAP breakMode string."""
        if self == ExceptionBreakpointMode.RAISED:
            return "always"
        if self == ExceptionBreakpointMode.UNHANDLED:
            return "unhandled"
        if self == ExceptionBreakpointMode.USER_UNHANDLED:
            return "userUnhandled"
        return "never"


class SessionState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


class StepDirection(Enum):
    INTO = "into"
    OVER = "over"
    OUT = "out"


class ThreadState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    UNKNOWN = "unknown"
