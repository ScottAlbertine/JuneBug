from annotations import ProjectPath
from db import get_db
from db_models import DBSession, DBSourcePosition
from frontend_models import DebugSession, DebuggerStatusResponse, SourcePosition


def get_debugger_status(projectPath: ProjectPath) -> DebuggerStatusResponse | str:
    """Returns the current status of the debugger including all active debug sessions.
Use this tool to get an overview of all running debug sessions and their states.

Preconditions:
- None.

Returns explicit `sessions[]` and `activeSessionId`.

Next call:
- If no sessions are running, call `start_debugger_session`.
- If multiple sessions are active, use returned `id` as `sessionId` in subsequent calls."""
    with get_db(projectPath):
        sessions: list[DebugSession] = []
        for db_session in DBSession.select(DBSession, DBSourcePosition).left_outer_join(DBSourcePosition):
            position: SourcePosition | None = None
            if db_session.current_position:
                position = SourcePosition(
                    filePath=db_session.current_position.file_path,
                    line=db_session.current_position.line_num,
                    column=db_session.current_position.column,
                )
            session = DebugSession(
                id=db_session.id,
                state=db_session.state,
                breakpointsMuted=db_session.breakpoints_muted,
                currentPosition=position,
            )
            sessions.append(session)
        return DebuggerStatusResponse(sessions=sessions)
