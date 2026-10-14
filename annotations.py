from typing import Annotated

from pydantic import BeforeValidator, Field
from pydantic_core import PydanticCustomError

NO_PROJECT_PATH_ERROR = """
You must specify the project path via `project_path` parameter when calling this tool.
If you're aware of the current working directory you may pass it as `project_path`.
In the case when it's unobvious which project to use you have to ASK the USER about which project to use.
"""


def validate_project_path(project_path: str | None) -> str:
    """Raise a nice custom error on an unspecified project path."""
    if not project_path:
        raise PydanticCustomError("missing", NO_PROJECT_PATH_ERROR)
    return project_path


ProjectPath = Annotated[
    str,
    Field(
        description="""
            The project path. Pass this value ALWAYS if you are aware of it. It reduces numbers of ambiguous calls.
            In the case you know only the current working directory you can use it as the project path.
            If you're not aware about the project path you can ask user about it.
        """,
    ),
    BeforeValidator(validate_project_path),
]

SessionID = Annotated[
    str | None,
    "Debug session ID. Use the current ID returned by `list_debugger_sessions` or `start_debugger_session`. "
    "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
    "If null and exactly one active session exists, it is selected automatically. "
    "If multiple sessions are active and session_id is omitted, the call fails. Default: null.",
]

FilePath = Annotated[
    str,
    "Path to the file. Supports project-relative paths, paths with '..', absolute paths, and URLs such as 'file://'.",
]

LineNum = Annotated[int, "1-based line number. The target location must be executable."]

FrameID = Annotated[
    int | None,
    "Stack frame id. Obtain this from the current paused `get_stack` result; "
    "do not reuse a cached frame id after `resume`, `step_*`, `run_to_line`, or any change in paused location. "
    "If null, uses the frame currently selected in the debugger, the first one `get_stack` returns. Default: null.",
]
