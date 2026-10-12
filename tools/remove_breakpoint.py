from typing import Annotated

from annotations import SessionID
from models import RemoveBreakpointResponse


def remove_breakpoint(
    session_id: SessionID,
    file_path: Annotated[
        str | None,
        "Optional input: Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, "
        "archive entries like '/path/lib.jar!/pkg/Foo.class', and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools).",
    ] = None,
    line: Annotated[int | None, "Optional input: line number (1-based) of the breakpoint to remove."] = None,
) -> RemoveBreakpointResponse:
    """Removes previously set breakpoints.

    Behavior:
    - Idempotent: removing a non-existing breakpoint does nothing.

    Next call:
    - Use `list_breakpoints` to verify the remaining set.
    """
    print(session_id)
    print(file_path)
    print(line)
