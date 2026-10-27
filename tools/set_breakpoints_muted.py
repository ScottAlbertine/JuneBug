from typing import Annotated

from pydantic import Field

from annotations import SessionID
from models import SessionStatus
import session_service
from utils import wait_for_timeout


async def set_breakpoints_muted(
    breakpoints_muted: Annotated[bool, "Session-wide breakpoint mute flag."],
    session_id: SessionID = None,
    timeout: Annotated[
        int, Field(description="Timeout in milliseconds to wait to mute all breakpoints. Default: 10000.", ge=0),
    ] = 10000,
) -> SessionStatus:
    """
    Enable or disable all breakpoints in a debug session without removing them.

    Use this to temporarily prevent the debugee from pausing at any breakpoint while
    keeping the breakpoint configuration intact. Useful for running through code quickly
    and then re-enabling breakpoints later.

    Preconditions:
    - A valid session must exist (may be running or paused).

    Behavior:
    - When muted (true): all breakpoints stop triggering immediately.
    - When unmuted (false): all breakpoints are restored and trigger normally again.
    - If the mute state is already at the requested value, this is a no-op.

    Next call guidance:
    - After muting, you can safely resume execution without hitting any breakpoints.
      Use run_to_line to jump to a specific location instead.
    - After unmuting, breakpoints will trigger on the next hit.
    - Breakpoints added while muted take effect once unmuted.
    """
    session = session_service.get_session(session_id)

    async def go() -> SessionStatus:
        await session.set_breakpoints_muted(breakpoints_muted)
        return await session.get_status()

    return await wait_for_timeout(go(), timeout)
