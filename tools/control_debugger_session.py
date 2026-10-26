from asyncio import wait_for
from typing import Annotated

from annotations import SessionID
from enums import Action, StepDirection
from models import SessionStatus
import session_service


async def control_debugger_session(
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
    Control the execution flow of a debug session: step, resume, pause, stop, or wait.

    This is the primary tool for driving execution during a debugging session.
    Choose the action that matches your debugging goal.

    Preconditions:
    - A valid, non-stopped session must exist. Operations on stopped sessions fail.
    - step_into, step_over, step_out require the session to be in a paused state.

    Behavior by action:
    - step_into: Steps one line into the current call. If the line calls a function,
      execution enters that function. Blocks until stepping is complete.
    - step_over: Steps one line, executing any function calls on that line without
      entering them. Blocks until stepping is complete.
    - step_out: Steps until the current function returns. Blocks until paused at the
      caller's next line.
    - resume: Resumes execution of all threads. Non-blocking — returns immediately.
      Does nothing if the session is already running.
    - pause: Interrupts execution of all threads. Blocks until all threads are paused.
      The session state becomes paused. Does nothing if the session is already paused.
    - stop: Terminates the debug session. Disconnects from the debugger and sends
      SIGTERM to the debugee process (for sessions launched by this server).
      The debugee may run to completion after this signal.
      No further tool calls can be made to this session_id after stop.
    - wait_for_pause: Blocks until the debugger pauses on its own (e.g., hits a
      breakpoint). Does not send any DAP commands. Use this after resume to wait
      for a breakpoint hit. If already paused, returns immediately.

    Next call guidance:
    - After step_* or pause: the session is paused. Use get_stack, list_variables,
      or evaluate_expression to inspect state, then step again or resume.
    - After resume: call wait_for_pause (with an appropriate timeout) to wait for
      the next breakpoint hit. Timeout guidance: step_* / pause usually 5000-15000ms;
      wait_for_pause usually 30000-120000ms depending on workload and breakpoints.
    - After stop: the session is dead. Launch a new session to continue debugging.
    """
    session = session_service.get_session(session_id)

    async def go() -> None:
        if action == Action.STEP_INTO:
            await session.step(StepDirection.INTO)
        elif action == Action.STEP_OVER:
            await session.step(StepDirection.OVER)
        elif action == Action.STEP_OUT:
            await session.step(StepDirection.OUT)
        elif action == Action.RESUME:
            await session.resume()
        elif action == Action.PAUSE:
            await session.pause()
        elif action == Action.STOP:
            await session.stop()
        elif action == Action.WAIT_FOR_PAUSE:
            await session.wait_for_pause()

    await wait_for(go(), timeout=timeout / 1000.0)

    return await session.get_status()
