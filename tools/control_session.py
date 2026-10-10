from typing import Annotated

from annotations import SessionID
from enums import Action
from models import SessionStatus
import session_service


def control_session(
    action: Annotated[
        Action,
        "Action to perform: STEP_INTO, STEP_OVER, STEP_OUT, RESUME, PAUSE, STOP, WAIT_FOR_PAUSE, DRAIN_EVENTS. "
        "Event draining is currently populated only by JVM-based debuggers (Java, Kotlin, etc.).",
    ],
    session_id: SessionID = None,
    timeout: Annotated[
        int,
        "Timeout in milliseconds to wait for action completion. "
        "Guidance: STEP_* / PAUSE usually 5000-15000; WAIT_FOR_PAUSE usually 30000-120000 depending on workload and breakpoints. "
        "Default: 30000.",
    ] = 30000,
) -> SessionStatus:
    """Controls the execution of a debug session.
Use this tool to step through code, resume execution, pause, or stop the debug session.

Preconditions:
- A debug session must exist.
- `STEP_*` requires a suspended session.

Actions:
- STEP_INTO: Step into the next method call
- STEP_OVER: Step over the current line
- STEP_OUT: Step out of the current method
- RESUME: Resume program execution until the next breakpoint
- PAUSE: Pause program execution
- STOP: Stop the debug session
- WAIT_FOR_PAUSE: Wait until the session pauses (breakpoint hit or paused manually)
- DRAIN_EVENTS: Drain tracepoint outputs for the session (breakpoint errors are drained for all actions)

Important notes:
- If the program is running, use WAIT_FOR_PAUSE or PAUSE before STEP_* / RESUME.
- Use a current `session_id` from `get_debugger_sessions` or `start_debugger_session`. If a session stops, times out, or disappears, refresh the session list before the next session-scoped call.
- RESUME does NOT set breakpoints. If there are no enabled breakpoints (or none will be hit next), the program may run to completion and the session may stop without pausing.
- After RESUME, call WAIT_FOR_PAUSE to confirm the next suspension. If WAIT_FOR_PAUSE times out, consider PAUSE and re-check breakpoints.
- `DRAIN_EVENTS` also requires an existing session; do not reuse a stale `session_id` after the session has terminated.

Next call:
- After `RESUME`, call `control_session(action=WAIT_FOR_PAUSE)`.
- After a paused result, call `get_stack` / `get_frame_values` / `evaluate_expression`.

State values in the result:
- running: Program is executing
- paused: Execution is suspended (breakpoint, step, or manual pause)
- stopped: Debug session has terminated
"""
    session = session_service.get_session(session_id)

    if action == Action.STEP_INTO:
        pass
    elif action == Action.STEP_OVER:
        pass
    elif action == Action.STEP_OUT:
        pass
    elif action == Action.RESUME:
        session.resume()
    elif action == Action.PAUSE:
        session.pause()
    elif action == Action.STOP:
        pass
    elif action == Action.WAIT_FOR_PAUSE:
        pass
    elif action == Action.DRAIN_EVENTS:
        pass

    return session.get_status()
