from enum import Enum


class Action(Enum):
    STEP_INTO = "step_into"
    STEP_OVER = "step_over"
    STEP_OUT = "step_out"
    RESUME = "resume"
    PAUSE = "pause"
    STOP = "stop"
    WAIT_FOR_PAUSE = "wait_for_pause"


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
    ALL = "all"
    THREAD = "thread"
    NONE = "none"


class ThreadState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    UNKNOWN = "unknown"
