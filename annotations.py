from typing import Annotated

from pydantic import BeforeValidator, Field
from pydantic_core import PydanticCustomError

from constants import NO_PROJECT_PATH_ERROR


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
    "Debug session ID. Use the current ID returned by `get_debugger_status` or `start_debugger_session`. "
    "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
    "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
    "If null and exactly one active session exists, it is selected automatically. "
    "If multiple sessions are active and session_id is omitted, the call fails. Default: null.",
]

FrameIndex = Annotated[
    int | None,
    "Stack frame index counted from the top of the stack, the same `index` `get_stack` reports: "
    "0 is the frame execution is in, 1 its caller, and so on. "
    "Obtain this from the current paused `get_stack` result; "
    "do not reuse a cached frame index after `RESUME`, `STEP_*`, `run_to_line`, or any change in paused location. "
    "If null, uses the frame currently selected in the debugger, the one `get_stack` marks `is_current`. Default: null.",
]
