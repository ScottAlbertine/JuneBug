from typing import Annotated

from annotations import SessionID
from enums import Action, StepDirection
from models import SessionStatus
import session_service


def control_debugger_session(
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
    """
    Controls the execution of a debug session.
    Use this tool to step through code, resume execution, pause, or stop the debug session.

    Preconditions:
    - A debug session must exist.
    - `step_*` actions require a suspended session.

    Actions:
    - step_into: Step into the next method call. Blocks until step is done.
    - step_over: Step over the current line. Blocks until step is done.
    - step_out: Step out of the current method. Blocks until step is done.
    - resume: Resume program execution. Does not block, program runs in the background after this tool call completes. Only use this when the program is paused.
    - pause: Pause program execution. Blocks until program is paused.
    - stop: Stop the debug session. Does not block. This attempts to terminate the debugee process, however, the debugee process may run to completion after this signal.
    - wait_for_pause: Wait until the program pauses due to breakpoint hit or program completion. Blocks until program is paused. Idempotent, does nothing if the program is already paused.

    Important notes:
    - Use a current `session_id` from one of the other debugger_session tools. If a session stops, times out, or disappears, refresh the session list before the next session-scoped call.
    - `resume` does NOT set breakpoints. If there are no enabled breakpoints (or none will be hit next), the program may run to completion and the session may stop without pausing.
    - If the program is running, use `wait_for_pause` or `pause` before `step_*` / `resume`.
    - If `wait_for_pause` times out, consider `pause` and re-check breakpoints.

    Next call:
    - After `resume`, call `control_debugger_session(action=wait_for_pause)` to confirm the next suspension.
    - After a paused result, call `get_stack` / `list_variables` / `evaluate_expression`.

    State values in the result:
    - running: Program is executing
    - paused: Execution is suspended (breakpoint, step, or manual pause)
    - stopped: Debug session has terminated
    """
    session = session_service.get_session(session_id)

    if action == Action.STEP_INTO:
        session.step(StepDirection.INTO)
    elif action == Action.STEP_OVER:
        session.step(StepDirection.OVER)
    elif action == Action.STEP_OUT:
        session.step(StepDirection.OUT)
    elif action == Action.RESUME:
        session.resume()
    elif action == Action.PAUSE:
        session.pause()
    elif action == Action.STOP:
        session.stop()
    elif action == Action.WAIT_FOR_PAUSE:
        session.wait_for_pause()

    return session.get_status()
