from typing import Annotated

from annotations import SessionID
from enums import Action
from models import SessionStatus
import session_service


def control_session(
    action: Annotated[
        Action, "Action to perform: step_into, step_over, step_out, resume, pause, stop, wait_for_pause.",
    ],
    session_id: SessionID = None,
    timeout: Annotated[
        int,
        "Timeout in milliseconds to wait for action completion. "
        "Guidance: step_* / pause usually 5000-15000; wait_for_pause usually 30000-120000 depending on workload and breakpoints. "
        "Default: 30000.",
    ] = 30000,
) -> SessionStatus:
    """Controls the execution of a debug session.
Use this tool to step through code, resume execution, pause, or stop the debug session.

Preconditions:
- A debug session must exist.
- `step_*` actions require a suspended session.

Actions:
- step_into: Step into the next method call
- step_over: Step over the current line
- step_out: Step out of the current method
- resume: Resume program execution until the next breakpoint
- pause: Pause program execution
- stop: Stop the debug session
- wait_for_pause: Wait until the session pauses (breakpoint hit or paused manually)

Important notes:
- If the program is running, use `wait_for_pause` or `pause` before `step_*` / `resume`.
- Use a current `session_id` from `get_debugger_sessions` or `start_debugger_session`. If a session stops, times out, or disappears, refresh the session list before the next session-scoped call.
- `resume` does NOT set breakpoints. If there are no enabled breakpoints (or none will be hit next), the program may run to completion and the session may stop without pausing.
- After `resume`, call `wait_for_pause` to confirm the next suspension. If `wait_for_pause` times out, consider `pause` and re-check breakpoints.

Next call:
- After `resume`, call `control_session(action=wait_for_pause)`.
- After a paused result, call `get_stack` / `get_frame_values` / `evaluate_expression`.

State values in the result:
- running: Program is executing
- paused: Execution is suspended (breakpoint, step, or manual pause)
- stopped: Debug session has terminated
"""
    # TODO: fix the above docsting
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
        session.wait_for_pause()

    return session.get_status()
