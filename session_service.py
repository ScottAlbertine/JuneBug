"""
Service module that manages a global index of sessions.
This is shared in-memory across threads, since it represents a single, universal, external state.
It can create, find, and eventually delete sessions.
"""
import subprocess
import uuid

from constants import TEMP_DIR
from exceptions import MissingSessionId, SessionNotFound
from session import Session
from utils import find_free_port, install_debugpy

# global index of live Session objects, available across all threads
SESSIONS: dict[str, Session] = {}


def get_session(session_id: str | None) -> Session:
    """
    Raises MissingSessionId if one isn't specified and there's more tha one session.
    Raises SessionNotFound if we can't find a client.
    """
    if not session_id:
        if len(SESSIONS) == 1:
            session_id = next(iter(SESSIONS.keys()))

    if not session_id:
        raise MissingSessionId()

    if session_id not in SESSIONS:
        raise SessionNotFound(session_id)

    return SESSIONS[session_id]


def get_sessions(project_path: str) -> list[Session]:
    """Get all sessions for a given project path."""
    return [session for session in SESSIONS.values() if session.project_path == project_path]


def attach_session(
    session_id: str, project_path: str, port: int, timeout: int, we_own: bool = False, pid: int | None = None
) -> Session:
    """Attach a new session to an existing python process, via DAP, on the given port."""
    session = Session(session_id, project_path, port, timeout, we_own, pid)
    SESSIONS[session_id] = session
    return session


def launch_session(
    project_path: str,
    python_path: str,
    file_path: str,
    timeout: int,
    program_arguments: list[str],
    working_directory: str | None,
    env: dict[str, str],
) -> Session:
    """Launch a new python process in debug mode, and attach a new session to it."""
    install_debugpy(python_path)

    session_id = str(uuid.uuid4())
    port = find_free_port()

    debugee = subprocess.Popen(
        args=[
            python_path,
            "-Xfrozen_modules=off",
            "-m", "debugpy",
            "--listen", f"{port}",
            "--wait-for-client",
            file_path,
            *program_arguments,
        ],
        stdout=open(TEMP_DIR / f"{session_id}.stdout.txt", "w"),
        stderr=open(TEMP_DIR / f"{session_id}.stderr.txt", "w"),
        cwd=working_directory or project_path,
        env=env,
    )

    return attach_session(session_id, project_path, port, timeout, we_own=True, pid=debugee.pid)
