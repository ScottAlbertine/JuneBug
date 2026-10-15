from typing import Annotated

ProjectPath = Annotated[
    str,
    """
    The project path.
    In the case you know only the current working directory you can use it as the project path.
    In the case when it's unobvious which project to use you have to ASK the USER about which project to use.
    """,
]

SessionID = Annotated[
    str | None,
    """
    Debug session ID. Use the current ID returned by the appropriate debugger_session tool.
    If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID.
    If null and exactly one active session exists, it is selected automatically.
    If multiple sessions are active and session_id is omitted, the call fails. Default: null.
    """,
]

FilePath = Annotated[
    str,
    "Path to the file. Supports project-relative paths, paths with '..', absolute paths, and URLs such as 'file://'.",
]

LineNum = Annotated[int, "1-based line number. The target location must be executable."]

FrameID = Annotated[
    int | None,
    """
    Stack frame id. Obtain this from the current paused `get_stack` result;
    do not reuse a cached frame id after `resume`, `step_*`, `run_to_line`, or any change in paused location.
    If null, uses the frame currently selected in the debugger, the first one `get_stack` returns. Default: null.
    """
]
