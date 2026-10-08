from typing import Annotated

from annotations import ProjectPath
from frontend_models import BreakpointsResponse


def list_breakpoints(
    projectPath: ProjectPath,
    filePath: Annotated[
        str | None,
        "Optional file path to filter breakpoints. Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, archive entries like "
        "'/path/lib.jar!/pkg/Foo.class', and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools). "
        "If not specified, returns all breakpoints. Default: null.",
    ] = None,
    sessionId: Annotated[
        str | None,
        "Debug session ID. Use the current ID returned by `get_debugger_status` or `start_debugger_session`. "
        "If a session has stopped, timed out, or disappeared, refresh the session list before reusing an old ID. "
        "Format: uses session name as ID by default; if multiple sessions share the same name, ID is `<sessionName>#<executionId>`. "
        "If null and exactly one active session exists, it is selected automatically. "
        "If multiple sessions are active and sessionId is omitted, the call fails. "
        "Default: null. "
        "Optional; when omitted, `breakpointsMuted` is returned only if exactly one active session exists.",
    ] = None,
) -> BreakpointsResponse:
    """Lists all breakpoints in the project or in a specific file.
Use this tool to see all currently set breakpoints and their properties.

Tip: Call this before RESUME to confirm there is at least one enabled breakpoint that is expected to be hit next.

Behavior:
- If `filePath` is provided, returns only breakpoints in that file.
- Returns rich attributes for each breakpoint (id, type, file, line, enabled, owner, condition, isLogMessage, isLogStack, temporary, suspendPolicy, hitCount).
- `breakpointsMuted` reports the session-wide debugger mute flag when a session is resolved; it does not change per-breakpoint `enabled` values.

Next call:
- If no suitable breakpoint exists, call `set_breakpoint`.
- Then continue execution with `control_session(action=RESUME)` and `control_session(action=WAIT_FOR_PAUSE)`."""
    print(filePath)
    print(sessionId)
    print(projectPath)
