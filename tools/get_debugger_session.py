from annotations import SessionID
from models import SessionStatus
import session_service


def get_debugger_session(session_id: SessionID = None) -> SessionStatus:
    """Returns the status of the given active debugger session."""
    return session_service.get_session(session_id).get_status()
