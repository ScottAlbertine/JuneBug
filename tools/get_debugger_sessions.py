from annotations import ProjectPath
from models import SessionStatuses
import session_service


def get_debugger_sessions(project_path: ProjectPath) -> SessionStatuses:
    """Returns the status of all active debugger sessions.

Preconditions:
- None.

Returns explicit `sessions[]`.

Next call:
- If no sessions are running, call `start_debugger_session`.
- If multiple sessions are active, use returned `id` as `session_id` in subsequent calls."""
    sessions = session_service.get_sessions(project_path)
    statuses = [session.get_status() for session in sessions]
    return SessionStatuses(sessions=statuses)
