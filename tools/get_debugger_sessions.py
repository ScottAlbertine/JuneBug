from annotations import ProjectPath
from db import get_db
from db_models import DBDebugSession, DBSourcePosition
from frontend_models import DebugSession, DebugSessions, SourcePosition


def get_debugger_sessions(projectPath: ProjectPath) -> DebugSessions | str:
    """Returns all active debugger sessions and their states.

Preconditions:
- None.

Returns explicit `sessions[]`.

Next call:
- If no sessions are running, call `start_debugger_session`.
- If multiple sessions are active, use returned `id` as `sessionId` in subsequent calls."""
    with get_db(projectPath):
        sessions = [
            DebugSession.from_db(session) for session in
            DBDebugSession.select(DBDebugSession, DBSourcePosition).left_outer_join(DBSourcePosition)
        ]
        return DebugSessions(sessions=sessions)
