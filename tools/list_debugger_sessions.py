from annotations import ProjectPath
from models import SessionStatuses
import session_service


def list_debugger_sessions(project_path: ProjectPath) -> SessionStatuses:
    """Returns all active debugger sessions that have the given project path.

    Next call:
    - If no sessions are running, call `launch_debugger_session` or `attach_debugger_session`.
    - If multiple sessions are active, use returned `id` as `session_id` in subsequent calls.
    """
    sessions = session_service.get_sessions(project_path)
    statuses = [session.get_status() for session in sessions]
    return SessionStatuses(sessions=statuses)
