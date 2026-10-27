from typing import Annotated

from pydantic import Field

from annotations import SessionID
from models import SessionStatus
import session_service
from utils import wait_for_timeout


async def get_debugger_session(
    session_id: SessionID = None,
    timeout: Annotated[
        int, Field(description="Timeout in milliseconds to wait to get the status. Default: 5000.", ge=0),
    ] = 5000,
) -> SessionStatus:
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
    return await wait_for_timeout(session_service.get_session(session_id).get_status(), timeout)
