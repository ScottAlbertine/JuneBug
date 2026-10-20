from annotations import FilePath, LineNum, SessionID
import session_service
from utils import normalize_file_path


def remove_breakpoint(file_path: FilePath, line: LineNum, session_id: SessionID = None) -> None:
    """
    Removes previously set breakpoints.

    Behavior:
    - Idempotent: removing a non-existing breakpoint does nothing.

    Next call:
    - Use `list_breakpoints` to verify the remaining set.
    """

    session = session_service.get_session(session_id)
    path = normalize_file_path(session.project_path, file_path)
    session.remove_breakpoint(path, line)
