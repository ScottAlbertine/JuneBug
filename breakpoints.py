"""Data structure for storing the tracked breakpoints under a given `Session`."""
from pathlib import Path

from dap import Event

from enums import BreakpointType, SuspendPolicy
from models import Breakpoint


class File:
    """A file, with breakpoints in it."""

    def __init__(self, path: Path):
        self.path = path
        self.breakpoints: dict[int, Breakpoint] = {}

    def add_breakpoint(self, breakpoint: Breakpoint) -> None:
        self.breakpoints[breakpoint.line] = breakpoint

    def get_breakpoints(self) -> list[Breakpoint]:
        return list(self.breakpoints.values())

    def get_breakpoint(self, line: int) -> Breakpoint | None:
        return self.breakpoints.get(line)


class Breakpoints:
    """
    Data structure for storing the tracked breakpoints under a given `Session`.

    The way DAP handles breakpoints is very stupid.
    It keeps an internal index of breakpoints, by IDs that it generates.
    It also keeps an internal index of breakpoints by file.
    However, you cannot request any of this information ever.
    You only have one method: `setBreakpoints`.
    That sets all breakpoints for the given file, and returns the list of all breakpoints for that file, with their generated IDs.
    Thus, we have to mirror both of those invisible internal indexes here, and keep them updated every time we set breakpoints.
    That way, we can actually support listing, and removing, breakpoints.
    """

    def __init__(self):
        # All breakpointed files, indexed by path
        self._files: dict[Path, File] = {}
        # All breakpoints, indexed by ID
        self._breakpoints: dict[int, Breakpoint] = {}

    def add_breakpoint(
        self, path: Path, line: int, condition: str | None, temporary: bool, suspend_policy: SuspendPolicy,
    ) -> Breakpoint:
        bp = Breakpoint(
            type=BreakpointType.LINE,
            file=path,
            line=line,
            condition=condition,
            temporary=temporary,
            suspend_policy=suspend_policy,
            hit_count=0,
        )
        self.get_file(path).add_breakpoint(bp)
        return bp

    def get_file(self, path: Path) -> File:
        """Gets the breakpointed file for the given path, creating a new one if needed."""
        return self._files.setdefault(path, File(path))

    def get_breakpoints_for_file(self, path: Path) -> list[Breakpoint]:
        return self.get_file(path).get_breakpoints()

    def get_breakpoint(self, path: Path, line: int) -> Breakpoint | None:
        return self.get_file(path).get_breakpoint(line)

    def refresh(self, dap_set_breakpoints_response: Event) -> None:
        """
        Refresh our registries of tracked breakpoints based DAP's response to a 'setBreakpoints' request.
        Right now, all we have to do here is set the newly returned IDs on `self._breakpoints`.
        In the future, we might need to add or remove breakpoints from our list of breakpoints in the file, as well, depending on what comes back.
        """
        for dap_breakpoint in dap_set_breakpoints_response.body["body"]["breakpoints"]:
            if not dap_breakpoint.get("verified", True):
                raise ValueError("Unverified breakpoint, figure out what's up with these.")
            bp = self.get_breakpoint(Path(dap_breakpoint["source"]["path"]), dap_breakpoint["line"])
            if bp is None:
                raise KeyError(
                    "New breakpoint returned from debugger that we weren't already tracking, figure out what's up with that.",
                )
            self._breakpoints[dap_breakpoint["id"]] = bp
