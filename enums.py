from enum import Enum


class Action(Enum):
    STEP_INTO = "step_into"
    STEP_OVER = "step_over"
    STEP_OUT = "step_out"
    RESUME = "resume"
    PAUSE = "pause"
    STOP = "stop"
    WAIT_FOR_PAUSE = "wait_for_pause"


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
