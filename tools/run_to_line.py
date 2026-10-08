from typing import Annotated

from annotations import ProjectPath, SessionID
from frontend_models import RunToLineResponse


def run_to_line(
    projectPath: ProjectPath,
    filePath: Annotated[
        str,
        "Target source file path. Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, archive entries like '/path/lib.jar!/pkg/Foo.class', "
        "and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools).",
    ],
    line: Annotated[int, "Target line number (1-based)."],
    sessionId: SessionID = None,
    timeout: Annotated[int, "Timeout in milliseconds waiting for paused/stopped result. Default: 30000."] = 30000,
) -> RunToLineResponse:
    """Resumes execution to a target line.
Use this tool to run until a specific source position without manually stepping.

Preconditions:
- Session must be suspended.
- Target file/line must be valid.

Outcome:
- paused: session paused at or after target.
- stopped: session terminated before pause.
- timeout: no pause/stop within timeout window.

Next call:
- If paused, call `get_stack` / `get_frame_values` / `evaluate_expression`.
- If the session stopped or disappeared, refresh `sessionId` via `get_debugger_status` before issuing another session-scoped call."""
    print(sessionId)
    print(filePath)
    print(line)
    print(timeout)
    print(projectPath)
