"""
Service module that manages a global index of sessions.
This is shared in-memory across threads, since it represents a single, universal, external state.
It can create, find, and eventually delete sessions.
"""
from pathlib import Path
import subprocess
import uuid

from constants import TEMP_DIR
from enums import SessionState
from exceptions import DirectoryNotFound, FileNotFound, MissingSessionId, SessionNotFound
from session import Session
from utils import find_free_port, install_debugpy


class Sessions(dict[str, Session]):
    """
    Global singleton index of live Session objects, available across all threads
    Has a 100 item limit, with the Least Recently Created item being dropped.
    This is specifically to avoid leaking memory when this MCP server is left running for weeks.
    It is its own class, rather than using `cachetools.FIFOCache` because we want to try and gracefully stop the sessions before dropping them.
    """
    LIMIT = 100

    def __setitem__(self, session_id: str, session: Session, /) -> None:
        super().__setitem__(session_id, session)

        if len(self) > self.LIMIT:
            # Python dicts are insertion ordered since 3.7
            oldest_session_id = next(iter(self))
            oldest_session = self[oldest_session_id]
            # try to stop the session, to be nice and clean up
            try:
                oldest_session.stop()
            except BaseException:
                pass  # no matter what happens, don't error, if we can't clean up, too bad.
            del self[oldest_session_id]


SESSIONS = Sessions()


def get_session(session_id: str | None) -> Session:
    """
    Raises MissingSessionId if one isn't specified and there's more than one non-stopped session.
    Raises SessionNotFound if we can't find a client.
    """
    if not session_id:
        active_sessions = {sid for sid, s in SESSIONS.items() if s.state != SessionState.STOPPED}
        if len(active_sessions) == 1:
            session_id = next(iter(active_sessions))

    if not session_id:
        raise MissingSessionId()

    if session_id not in SESSIONS:
        raise SessionNotFound(session_id)

    return SESSIONS[session_id]


def get_sessions(project_path: Path | None) -> list[Session]:
    """Get all sessions for a given project path."""
    return [session for session in SESSIONS.values() if project_path is None or session.project_path == project_path]


def attach_session(
    session_id: str,
    project_path: Path,
    host: str,
    port: int,
    timeout: float,
    we_own: bool = False,
    pid: int | None = None,
) -> Session:
    """Attach a new session to an existing python process, via DAP, on the given port."""
    session = Session(session_id, project_path, host, port, timeout, we_own, pid)
    SESSIONS[session_id] = session
    return session


def launch_session(
    project_path: Path,
    python_path: str,
    file_path: Path,
    timeout: float,
    program_arguments: list[str],
    working_directory: Path | None,
    env: dict[str, str],
) -> Session:
    """Launch a new python process in debug mode, and attach a new session to it."""
    install_debugpy(python_path)

    if not project_path.is_dir():
        raise DirectoryNotFound(project_path)
    if not file_path.exists():
        raise FileNotFound(file_path)
    if working_directory is not None and not working_directory.is_dir():
        raise DirectoryNotFound(working_directory)

    session_id = str(uuid.uuid4())
    port = find_free_port()

    debugee = subprocess.Popen(
        args=[
            python_path,
            "-Xfrozen_modules=off",
            "-m", "debugpy",
            "--listen", f"{port}",
            "--wait-for-client",
            str(file_path),
            *program_arguments,
        ],
        stdout=open(TEMP_DIR / f"{session_id}.stdout.txt", "w"),
        stderr=open(TEMP_DIR / f"{session_id}.stderr.txt", "w"),
        cwd=working_directory or project_path,
        env=env,
    )

    return attach_session(session_id, project_path, "127.0.0.1", port, timeout, we_own=True, pid=debugee.pid)
