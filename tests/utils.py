import re
import signal

import psutil


class MatchAny:
    """Fake object that matches any object of the given type."""

    def __init__(self, t: type):
        self.t = t

    def __eq__(self, o: object) -> bool:
        return isinstance(o, self.t)

    def __repr__(self) -> str:
        return f"any {self.t}"


class MatchRegex:
    """Fake object that matches a string based on the given regular expression."""

    def __init__(self, regex: str):
        self.regex = regex
        self.pattern = re.compile(regex)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, str):
            return False
        return self.pattern.match(o) is not None

    def __repr__(self) -> str:
        return f"r'{self.regex}'"


def kill_processes_by_module(module_names: list[str]) -> None:
    """Kill all processes whose command line contains any of the given module names."""
    for proc in psutil.process_iter(["pid", "cmdline"]):
        cmdline = proc.info["cmdline"] or []
        cmdline_str = " ".join(cmdline)
        if any(mod in cmdline_str for mod in module_names):
            try:
                proc.send_signal(signal.SIGTERM)
            except psutil.NoSuchProcess:
                pass
