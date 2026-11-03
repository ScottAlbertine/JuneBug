"""Data structure for storing the tracked exception breakpoints under a given `Session`."""
from typing import Any

from enums import ExceptionBreakpointMode
from models import ExceptionBreakpoint


class ExceptionBreakpoints:
    """
    Data structure for storing the tracked exception breakpoints under a given `Session`.

    The way DAP handles exception breakpoints is very stupid.
    It keeps a global internal list of exception breakpoints, but you can never read it, only set it.
    Thus, we need to keep a copy on our side to allow addition, listing, and deletion.
    """

    def __init__(self):
        self._breakpoints: list[ExceptionBreakpoint] = []

    def add_breakpoint(self, exception_type: str, mode: ExceptionBreakpointMode) -> ExceptionBreakpoint:
        """Create an exception breakpoint and track it appropriately."""
        bp = ExceptionBreakpoint(exception_type=exception_type, mode=mode)
        if bp not in self._breakpoints:  # dedupe. Yes this is O(n), this list will always be small.
            self._breakpoints.append(bp)
        return bp

    def list_all(self) -> list[ExceptionBreakpoint]:
        """List all tracked exception breakpoints."""
        return self._breakpoints

    def to_dap(self) -> list[dict[str, Any]]:
        """Turn all tracked exception breakpoints into a form that DAP can understand."""
        return [bp.to_dap() for bp in self._breakpoints]

    def remove_breakpoint(self, exception_type: str, mode: ExceptionBreakpointMode) -> None:
        """Remove an exception breakpoint. Idempotent, no-op on nonexistent exception breakpoint."""
        try:
            self._breakpoints.remove(ExceptionBreakpoint(exception_type=exception_type, mode=mode))
        except ValueError:
            pass
