from annotations import ProjectPath
from db import get_db
from db_models import DBDebugSession, DBSourcePosition
from frontend_models import DebugSession, DebugSessions


def get_debugger_sessions(project_path: ProjectPath) -> DebugSessions:
    """Returns all active debugger sessions and their states.

Preconditions:
- None.

Returns explicit `sessions[]`.

Next call:
- If no sessions are running, call `start_debugger_session`.
- If multiple sessions are active, use returned `id` as `session_id` in subsequent calls."""
    with get_db(project_path):
        sessions = [
            DebugSession.from_db(session) for session in
            DBDebugSession.select(DBDebugSession, DBSourcePosition).left_outer_join(DBSourcePosition)
        ]
        return DebugSessions(sessions=sessions)
