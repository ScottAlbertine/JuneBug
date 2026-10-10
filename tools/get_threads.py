from typing import Annotated

from annotations import SessionID
from models import ThreadsResponse
import session_service


def get_threads(
    session_id: SessionID = None,
    limit: Annotated[int, "Page size. Default: 50, max: 200."] = 50,
    offset: Annotated[int, "Page offset. Default: 0."] = 0,
) -> ThreadsResponse:
    """Returns the list of threads in the debug session.
Use this tool to see all threads and their current status.

Next call:
- Use `get_stack` for the selected thread.

Pagination:
- `offset`/`limit` are applied after collecting all stacks.

Ordering:
- By id

Schema fields: id, name, state, is_current.
"""

    session = session_service.get_session(session_id)
    threads = session.get_threads()
    return ThreadsResponse(threads=threads[offset:offset + limit], total_count=len(threads))
