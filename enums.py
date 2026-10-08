from enum import Enum


class Action(Enum):
    STEP_INTO = "STEP_INTO"
    STEP_OVER = "STEP_OVER"
    STEP_OUT = "STEP_OUT"
    RESUME = "RESUME"
    PAUSE = "PAUSE"
    STOP = "STOP"
    WAIT_FOR_PAUSE = "WAIT_FOR_PAUSE"
    DRAIN_EVENTS = "DRAIN_EVENTS"


class BreakpointOwner(Enum):
    USER = "user"
    AGENT = "agent"


class DebuggerEventType(Enum):
    BREAKPOINT_ERROR = "BREAKPOINT_ERROR"
    TRACEPOINT_OUTPUT = "TRACEPOINT_OUTPUT"


class DebuggerOutcome(Enum):
    PAUSED = "paused"
    STOPPED = "stopped"
    TIMEOUT = "timeout"


class DebuggerState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class SuspendPolicy(Enum):
    ALL = "ALL"
    THREAD = "THREAD"
    NONE = "NONE"
