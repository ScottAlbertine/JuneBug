from typing import Annotated

from annotations import FilePath, LineNum, SessionID
from enums import SuspendPolicy
from models import Breakpoint
import session_service
from utils import normalize_file_path


def set_breakpoint(
    file_path: FilePath,
    line: LineNum,
    session_id: SessionID = None,
    condition: Annotated[
        str | None,
        "Optional condition expression - breakpoint will only trigger when this evaluates to true. Default: null.",
    ] = None,
    temporary: Annotated[bool, "Temporary breakpoint (removed after first hit). Default: false."] = False,
    suspend_policy: Annotated[SuspendPolicy, "Suspend policy: all, thread, none. Default: all."] = SuspendPolicy.ALL,
) -> Breakpoint:
    """
    Creates a breakpoint.

    Event reporting:
    - Successful line-breakpoint responses also include `line_text`, a truncated excerpt of the actual source line where the breakpoint now resides. Inspect it to confirm placement before resuming.

    Apply semantics:
    - Provided fields are applied as the resulting state for the target breakpoint.
    - `condition=null` clears existing condition.

    Next call:
    - Use returned `line_text` and/or `list_breakpoints` to verify placement.
    - Continue execution via `control_session(action=resume)`.
    """
    session = session_service.get_session(session_id)
    path = normalize_file_path(session.project_path, file_path)
    return session.set_breakpoint(path, line, condition, temporary, suspend_policy)
