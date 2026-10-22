from typing import Annotated

from pydantic import Field

from annotations import SessionID
from models import ThreadsResponse
import session_service


def list_threads(
    session_id: SessionID = None,
    limit: Annotated[int, Field(description="Page size. Default: 50, max: 200.", ge=1)] = 50,
    offset: Annotated[int, Field(description="Page offset. Default: 0.", ge=0)] = 0,
) -> ThreadsResponse:
    """
    List all threads in a debug session, with pagination support.

    Returns the threads tracked by the session, reflecting their current state
    (running/paused/unknown) and which one is currently selected.

    Preconditions:
    - A valid, non-stopped session must exist.

    Behavior:
    - Results are paginated: `offset` skips that many threads, `limit` caps the
      number returned. `total_count` gives the full count for pagination math.
    - Each thread shows its id, name, state, and whether it is the current thread.

    Next call guidance:
    - Use a thread's `id` with `get_stack` to inspect its call stack.
    - Call this after resuming or pausing to see updated thread states.
    """
    session = session_service.get_session(session_id)
    threads = session.list_threads()
    return ThreadsResponse(threads=threads[offset:offset + limit], total_count=len(threads))
