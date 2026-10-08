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
        active_session_id: str | None = None
        for session in DBSession.select(DBSession, DBSourcePosition).join(DBSourcePosition):
            if session.is_active:
                active_session_id = session.id
            sessions.append(
                DebugSession(
                    id=session.id,
                    name=session.name,
                    state=session.state,
                    runConfigurationName=session.run_configuration_name,
                    breakpointsMuted=session.breakpoints_muted,
                    currentPosition=SourcePosition(
                        filePath=session.current_position.file_path,
                        line=session.current_position.line_num,
                        column=session.current_position.column,
                    ),
                ),
            )
        return DebuggerStatusResponse(sessions=sessions, activeSessionId=active_session_id)
