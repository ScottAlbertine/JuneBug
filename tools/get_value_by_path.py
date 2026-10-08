from typing import Annotated

from annotations import FrameIndex, ProjectPath, SessionID


def get_value_by_path(
    path: Annotated[
        list[str],
        "List of child names to navigate through, e.g. ['myObject', 'field', 'subField'] or ['items', '[0]', 'name']. "
        "Use exact node names from the current paused `get_frame_values` / `get_value_by_path` output "
        "and refresh stale path tokens after the paused location changes."
    ],
    sessionId: SessionID = None,
    frameIndex: FrameIndex = None,
    depth: Annotated[
        int,
        "Maximum depth for expanding children of the resolved value "
        "(0 = value only, 1 = immediate children, 2 = children + grandchildren, etc.). Default: 0."
    ] = 0,
    projectPath: ProjectPath = None,
) -> None:
    """Gets the value of a nested object by following a path of property names.
Use this tool to drill down into complex objects and inspect their nested properties.

Preconditions:
- Session must be suspended.
- Path must be non-empty and refer to names visible in the selected frame/object.

The result is returned as:
- depth == 0: just the presentation of the value at the specified path
- depth > 0: the presentation of the value plus a pseudo-graphics tree of its children up to the requested depth

Example: To get the value of obj.field.subField, use path = ["obj", "field", "subField"].
For array/list indexers, pass the index token as a regular path element (child name), e.g.
items[0].name -> path = ["items", "[0]", "name"].
Use exact child names from the current paused `get_frame_values` / previous `get_value_by_path` output
because index node names may differ by language/debugger (for example, "[0]" vs "0").
Refresh `path` tokens after `RESUME`, `STEP_*`, `run_to_line`, or any other change in paused location.

Next call:
- Use another `get_value_by_path` call to continue drilling deeper.
- Use `evaluate_expression` when direct name-path navigation is insufficient."""
    print(sessionId)
    print(frameIndex)
    print(path)
    print(depth)
    print(projectPath)

