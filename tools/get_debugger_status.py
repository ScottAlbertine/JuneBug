from annotations import ProjectPath
from models import DebuggerStatusResponse


def get_debugger_status(projectPath: ProjectPath = None) -> DebuggerStatusResponse:
    """Returns the current status of the debugger including all active debug sessions.
Use this tool to get an overview of all running debug sessions and their states.

Preconditions:
- None.

Returns explicit `sessions[]` and `activeSessionId`.

Next call:
- If no sessions are running, call `start_debugger_session`.
- If multiple sessions are active, use returned `id` as `sessionId` in subsequent calls."""
    print(projectPath)
