from enum import Enum


# TODO: unify enum caseing


class Action(Enum):
    STEP_INTO = "STEP_INTO"
    STEP_OVER = "STEP_OVER"
    STEP_OUT = "STEP_OUT"
    RESUME = "RESUME"
    PAUSE = "PAUSE"
    STOP = "STOP"
    WAIT_FOR_PAUSE = "WAIT_FOR_PAUSE"


class BreakpointType(Enum):
    LINE = "line"
    EXCEPTION = "exception"
    OTHER = "other"


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


class ThreadState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    UNKNOWN = "unknown"
