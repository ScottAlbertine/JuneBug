from typing import Annotated
import uuid

from pydantic import Field

from annotations import ProjectPath
from exceptions import AbsolutePathError
from models import SessionStatus
import session_service
from utils import normalize_file_path, wait_for_timeout


async def attach_debugger_session(
    project_path: ProjectPath,
    port: Annotated[int, Field("Port to attach a new debugger session to.", ge=0)],
    host: Annotated[str, "Host address to attach a new debugger session to."] = "127.0.0.1",
    timeout: Annotated[
        int, Field(
            description="Timeout in milliseconds to wait for the debug session to connect. Default: 60000.", ge=0,
        ),
    ] = 60000,
) -> SessionStatus:
    """
    Attach a debugger to an already-running Python process that is listening for debug connections.

    Use this when a program has already been started with debugpy (e.g., via
    `python -m debugpy --listen <port> --wait-for-client script.py`) and is waiting
    for a debugger to connect. Unlike launch_debugger_session, this does not spawn a
    new process — it connects to an existing one.

    Preconditions:
    - A Python process must already be running with debugpy attached, listening on
      the specified host and port.
    - The project_path should point to the project containing the debugee's source.

    Behavior:
    - Generates a new session ID and connects to the debuggee over TCP.
    - The session starts in an unknown state (the debugee may already be running or paused).
    - Unlike launched sessions, attached sessions do not capture stdout/stderr
      (those fields are null in the returned status).
    - Blocks until the connection is established or the timeout expires.

    Next call guidance:
    - Use the returned session_id for all subsequent debugger calls.
    - Since the process could be running or paused, call control_debugger_session to resume or pause it,
      to get it to the state you want before attempting to inspect.
    """
    session_id = str(uuid.uuid4())

    try:
        normal_project_path = normalize_file_path(project_path)
    except ValueError:
        raise AbsolutePathError("project_path")

    async def go() -> SessionStatus:
        session = await session_service.attach_session(session_id, normal_project_path, host, port)
        return await session.get_status()

    return await wait_for_timeout(go(), timeout)
