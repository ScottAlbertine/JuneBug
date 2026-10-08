from typing import Annotated

ProjectPath = Annotated[
    str | None,
    "The project path. Pass this value ALWAYS if you are aware of it. It reduces numbers of ambiguous calls. \n "
    "In the case you know only the current working directory you can use it as the project path.\n "
    "If you're not aware about the project path you can ask user about it."
]

SessionID = Annotated[
    str | None,
    "Debug session ID. Use the current ID returned by `get_debugger_status` or `start_debugger_session`. "
    "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
    "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
    "If null and exactly one active session exists, it is selected automatically. "
    "If multiple sessions are active and sessionId is omitted, the call fails. Default: null."
]

FrameIndex = Annotated[
    int | None,
    "Stack frame index counted from the top of the stack, the same `index` `get_stack` reports: "
    "0 is the frame execution is in, 1 its caller, and so on. "
    "Obtain this from the current paused `get_stack` result; "
    "do not reuse a cached frame index after `RESUME`, `STEP_*`, `run_to_line`, or any change in paused location. "
    "If null, uses the frame currently selected in the debugger, the one `get_stack` marks `isCurrent`. Default: null."
]
