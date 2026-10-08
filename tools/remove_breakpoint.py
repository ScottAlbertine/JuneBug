from typing import Annotated, Any

from annotations import ProjectPath
from enums import BreakpointOwner


def remove_breakpoint(
    breakpointId: Annotated[
        str | None, "Canonical breakpoint ID returned by `set_breakpoint` or `list_breakpoints`."] = None,
    filePath: Annotated[
        str | None,
        "Optional input: Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, "
        "archive entries like '/path/lib.jar!/pkg/Foo.class', and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools)."
    ] = None,
    line: Annotated[int | None, "Optional input: line number (1-based) of the breakpoint to remove."] = None,
    owner: Annotated[BreakpointOwner, "Breakpoint owner filter. Default: agent."] = BreakpointOwner.AGENT,
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'removed': {
    #       'type': 'boolean',
    #       'description': 'Whether at least one breakpoint was removed.'
    #     },
    #     'removedCount': {
    #       'type': 'integer',
    #       'description': 'Number of breakpoints removed at the requested location.'
    #     },
    #     'breakpointId': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Removed breakpoint ID when operation targeted one ID.'
    #     },
    #     'totalBreakpoints': {
    #       'type': 'integer',
    #       'description': 'Current total number of breakpoints after removal.'
    #     },
    #     'message': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Additional note when no matching breakpoint is found.'
    #     }
    #   },
    #   'required': [
    #     'removed',
    #     'removedCount',
    #     'totalBreakpoints'
    #   ],
    #   'type': 'object'
    # }
    """Removes breakpoints filtered by owner and optional selectors.
Use this tool to remove previously set breakpoints.

Behavior:
- `owner` defaults to `agent`.
- If only `owner` is provided, removes all breakpoints of that owner.
- If `breakpointId` is provided, removes matching breakpoint(s) for the selected owner.
- If `filePath`+`line` are provided, removes matching line breakpoint(s) for the selected owner.
- If multiple selectors are provided, all of them are combined (logical AND).
- Idempotent: removing a non-existing breakpoint returns removed=false.
- To remove all breakpoints regardless of owner, call twice: once with `owner=user`, once with `owner=agent`.

Next call:
- Use `list_breakpoints` to verify the remaining set."""
    print(breakpointId)
    print(filePath)
    print(line)
    print(owner)
    print(projectPath)

