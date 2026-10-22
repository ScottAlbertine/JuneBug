from annotations import SessionID
from models import SessionStatus
import session_service


def get_debugger_session(session_id: SessionID = None) -> SessionStatus:
    """
    Get the current status of a single debug session.

    Use this to check the state of a session without performing any debugging action.

    Preconditions:
    - A valid session must exist. If session_id is not provided and exactly one
      session is active, it is auto-selected. If multiple sessions exist and no
      session_id is given, the call fails.

    Behavior:
    - Returns the session's current state (running/paused/stopped/unknown), debugee
      PID, stdout/stderr capture file paths (for launched sessions), and breakpoint
      mute status.
    - If the session is paused, the current_position field shows where execution
      halted (file, line, and source text).

    Next call guidance:
    - Check the state field to decide what operations are valid: paused sessions
      can step, inspect variables, and evaluate expressions; running sessions can
      be paused or stopped.
    - Use the returned session_id in subsequent tool calls.
    - If the state is "stopped", start a new session instead of retrying.
    """
    return session_service.get_session(session_id).get_status()
