from typing import Annotated

from annotations import FilePath, LineNum, SessionID
from models import SessionStatus
import session_service
from utils import normalize_file_path


def run_to_line(
    file_path: FilePath,
    line: LineNum,
    session_id: SessionID = None,
    timeout: Annotated[int, "Timeout in milliseconds waiting for paused/stopped result. Default: 30000."] = 30000,
) -> SessionStatus:
    """
    Runs the program until it reaches a target line.
    Use this tool when you want to ignore all other breakpoints, and just run until you get to a given location.
    This tool sets a temporary breakpoint at the given location, then resumes execution.
    It then skips past all other breakpoints until it hits the breakpoint it set.
    The tool does block until that happens, just like `control_debugger_session(action=wait_for_pause)`.

    Outcome:
    If the debugger status is `stopped`, it is reasonable to conclude that the program ran to completion without hitting the given line.

    Next call:
    - If paused, call `get_stack` / `list_variables` / `evaluate_expression`.
    - If the session stopped, create a new one before issuing another session-scoped call.
    """
    session = session_service.get_session(session_id)
    path = normalize_file_path(session.project_path, file_path)
    session.run_to_line(path, line)
    return session.get_status()
