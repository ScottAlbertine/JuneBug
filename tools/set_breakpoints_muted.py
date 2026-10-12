from typing import Annotated

from annotations import SessionID
from models import SessionStatus
import session_service


def set_breakpoints_muted(
    breakpoints_muted: Annotated[bool, "Session-wide breakpoint mute flag."], session_id: SessionID = None
) -> SessionStatus:
    """
    Mutes or unmutes all breakpoints for the given session.
    Returns the status for the session, which includes the current breakpoint muting status.
    """
    session = session_service.get_session(session_id)
    session.set_breakpoints_muted(breakpoints_muted)
    return session.get_status()
