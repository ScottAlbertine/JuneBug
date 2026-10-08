from enum import Enum


# TODO: probably a better name needed here
class ActionEnum(Enum):
    STEP_INTO = "STEP_INTO"
    STEP_OVER = "STEP_OVER"
    STEP_OUT = "STEP_OUT"
    RESUME = "RESUME"
    PAUSE = "PAUSE"
    STOP = "STOP"
    WAIT_FOR_PAUSE = "WAIT_FOR_PAUSE"
    DRAIN_EVENTS = "DRAIN_EVENTS"

class DebuggerStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

class DebuggerOutcome(Enum):
    PAUSED = "paused"
    STOPPED = "stopped"
    TIMEOUT = "timeout"

# TODO: probably a better name needed here
class BreakpointEventType(Enum):
    BREAKPOINT_ERROR = "BREAKPOINT_ERROR"
    TRACEPOINT_OUTPUT = "TRACEPOINT_OUTPUT"

class BreakpointOwner(Enum):
    USER = "user"
    AGENT = "agent"

class SuspendPolicy(Enum):
    ALL = "ALL"
    THREAD = "THREAD"
    NONE = "NONE"