from annotations import ProjectPath
from models import SessionStatuses
import session_service


def list_debugger_sessions(project_path: ProjectPath) -> SessionStatuses:
    """
    List all debug sessions for a given project.

    Use this to discover which debug sessions exist before operating on them.

    Preconditions:
    - At least one debug session must have been created via launch_debugger_session
      or attach_debugger_session for the given project_path.

    Behavior:
    - Returns the status of every session associated with the project_path.
    - Each status includes the session_id, current state (running/paused/stopped/unknown),
      debugee PID, and breakpoint mute status.
    - Stopped sessions are still listed. Refresh this list before reusing an old session_id,
      as sessions may have terminated.

    Next call guidance:
    - Pick a session_id from the results to use in other debugger tools.
    - If only one non-stopped session exists, you can omit session_id in most
      tool calls and the server will auto-select it.
    - Call this tool periodically to check if a session has stopped before
      attempting further operations.
    """
    sessions = session_service.get_sessions(project_path)
    statuses = [session.get_status() for session in sessions]
    return SessionStatuses(sessions=statuses)
