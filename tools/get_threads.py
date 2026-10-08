from typing import Annotated

from annotations import ProjectPath, SessionID
from models import ThreadsResponse


def get_threads(
    sessionId: SessionID = None,
    limit: Annotated[int, "Page size. Default: 50, max: 200."] = 50,
    offset: Annotated[int, "Page offset. Default: 0."] = 0,
    projectPath: ProjectPath = None,
) -> ThreadsResponse:
    """Returns the list of threads in the debug session.
Use this tool to see all threads and their current status.

Preconditions:
- Session must be suspended.

Next call:
- Use `get_stack` for the selected thread.

Pagination:
- `offset`/`limit` are applied after collecting all stacks.

Ordering:
- Active thread first.
- Remaining threads are sorted by descending stack depth.

Schema fields: id, name, state, isCurrent, additionalInfo, additionalInfoTooltip, frameCount.
`additionalInfo`/`additionalInfoTooltip` use additional display info when available."""
    print(sessionId)
    print(limit)
    print(offset)
    print(projectPath)
