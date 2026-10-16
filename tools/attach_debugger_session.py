from typing import Annotated
import uuid

from pydantic import Field

from annotations import ProjectPath
from models import SessionStatus
import session_service


def attach_debugger_session(
    project_path: ProjectPath,
    port: Annotated[int, Field("Port to attach a new debugger session to.", ge=0)],
    host: Annotated[str, "Host address to attach a new debugger session to."] = "127.0.0.1",
    timeout: Annotated[
        int, Field(
            description="Timeout in milliseconds to wait for the debug session to connect. Default: 60000.", ge=0,
        ),
    ] = 60000,
) -> SessionStatus:
    # TODO: once all the remaining tool docstrings are finalized, have Junie generate this one.
    session_id = str(uuid.uuid4())
    session = session_service.attach_session(session_id, project_path, host, port, timeout)
    return session.get_status()
