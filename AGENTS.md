# JuneBug — Agent Notes

## Python Toolchain

This is a `direnv` project (`.envrc` uses `layout python3`). The Python virtual environment lives at `.direnv/python-3.14/`.

## Main Code

JuneBug is a [FastMCP](https://github.com/PrefectHQ/fastmcp) server that exposes 15 debugger tools over the MCP protocol. It wraps Python's DAP (Debug Adapter Protocol) implementation (`debugpy`/`dap`) to provide local and remote debugging capabilities.

### Architecture Overview

The code flows in four layers, top to bottom:

1. **`main.py`** — FastMCP entry point. Creates the server (`FastMCP("JuneBug MCP Server")`), registers all 15 tools via `mcp.tool()`, and runs on HTTP transport at `127.0.0.1:9000`.
2. **`tools/`** — 15 individual tool modules. Each is a plain function with `Annotated` parameters (from `annotations.py`) and a Pydantic model return type. Tools delegate to `session_service` or `Session`.
3. **`session.py`** — Central orchestrator. Owns a `DAPClient`, manages session state (`SessionState` enum), handles breakpoints/threads/variables/stepping, and processes DAP events via `_handle_event()`.
4. **`dap_client.py`** — DAP wrapper. Wraps the `dap` library's `DAPClient`, manages TCP socket lifecycle, auto-handles the initialize/attach handshake, and provides a send-then-pull pattern for every DAP command.

### Core Modules

- **`session_service.py`** — Global session registry. Maintains `SESSIONS: dict[str, Session]` (shared in-memory across threads). Functions: `get_session()` (auto-selects if only one exists), `get_sessions()` (by project path), `attach_session()` (connect to existing process), `launch_session()` (spawns debugpy subprocess via `subprocess.Popen`).
- **`breakpoints.py`** — `Breakpoints` class mirrors DAP's invisible internal indexes. Two dicts: files-by-path and breakpoints-by-id. DAP only exposes `setBreakpoints` and never lets you query back, so we track everything ourselves. `File` class holds breakpoints per-file, sorted by line. `refresh()` updates IDs from DAP responses.
- **`threads.py`** — `Threads` class mirrors DAP's thread state. Tracks threads by ID, manages state via `refresh()` from `threads` requests and `update()` from thread events (started/paused/exited). Handles `allThreadsStopped`/`allThreadsContinued` broadcasts.
- **`models.py`** — Pydantic `BaseModel` classes with detailed `Field` descriptions. Models: `Breakpoint` (with `to_dap()` and `floating()` factory), `Variable` (with `from_dap()`), `SessionStatus`, `StackFrame`, `Thread`, `StackFrames`, `ThreadsResponse`, `BreakpointsResponse`, `RunToLineResponse`, `SetVariableResponse`, `Variables`, `SessionStatuses`. All use `Annotated` with `Field` for MCP schema generation.
- **`enums.py`** — Six enums: `Action` (step_into/over/out, resume, pause, stop, wait_for_pause), `BreakpointType` (line/exception/other), `DebuggerOutcome` (paused/stopped/timeout), `SessionState` (running/paused/stopped/unknown), `StepDirection` (into/over/out), `ThreadState` (running/paused/unknown).
- **`exceptions.py`** — Custom exceptions with descriptive messages: `DebugpyInstallationFailed`, `DAPError` (wraps `ErrorResponse`), `FileNotFound`, `FrameNotFound`, `LineNotFound`, `MissingSessionId`, `SessionNotFound`, `SessionStateError`, `SessionStoppedError`, `ThreadNotFound`. These bubble up through FastMCP as `ToolError`.
- **`annotations.py`** — Shared `Annotated` parameter types reused across tools: `ProjectPath`, `SessionID` (nullable, auto-selects on single session), `FilePath` (supports relative, absolute, `file://`), `LineNum` (1-based), `FrameID` (nullable, defaults to current frame).
- **`constants.py`** — `TEMP_DIR = Path(gettempdir())` for stdout/stderr temp files.
- **`utils.py`** — `install_debugpy()` (checks and pip-installs), `find_free_port()` (socket bind trick), `connect_socket()` (retry loop, 100ms intervals), `normalize_file_path()` (handles relative/absolute/`file://`), `fetch_line_text()` (uses `islice` for single-line read).

### Tool Pattern

Every tool in `tools/` follows the same pattern:

1. Import shared types from `annotations.py`, enums from `enums.py`, models from `models.py`, and `session_service`.
2. Define a function with `Annotated` parameters and a Pydantic model return type.
3. Write a comprehensive docstring with sections: description, preconditions, behavior, next call guidance.
4. Call `session_service.get_session(session_id)` to resolve the session.
5. Delegate to `session.some_method()` and return the result.

Tools that don't need a session (e.g., `list_debugger_sessions`) call `session_service` directly. Tools that create sessions (`launch_debugger_session`, `attach_debugger_session`) call the appropriate factory and return `session.get_status()`.

### Tool Implementation Status

**Implemented** (12 tools): `launch_debugger_session`, `attach_debugger_session`, `get_debugger_session`, `list_debugger_sessions`, `control_debugger_session`, `set_breakpoint`, `list_breakpoints`, `remove_breakpoint`, `set_breakpoints_muted`, `list_threads`, `get_stack`, `list_variables`.

**Stubs** (4 tools): `evaluate_expression`, `get_value_by_path`, `run_to_line`, `set_variable`. These have complete docstrings and parameter annotations but only `print()` their arguments. They need implementation.

### Key Design Decisions

- **DAP Mirroring**: Both `Breakpoints` and `Threads` exist because DAP only gives you `setBreakpoints` and `threads()` — no way to query back. We maintain our own indexes and refresh on every DAP response.
- **Session State**: `Session` tracks `SessionState` (running/paused/stopped/unknown) and enforces it via `assert_state()` before operations that require a specific state.
- **Floating Breakpoints**: `Breakpoint.floating()` creates a temporary "you are here" marker used for pause/step operations. It's not a real DAP breakpoint.
- **`configuration_done()`**: Called exactly once per session, inside `resume()`. It auto-resumes all threads.
- **`we_own` flag**: Sessions launched by JuneBug own the debugee process. On `stop()`, they send `SIGTERM` via `psutil`. Attached sessions don't.
- **Stack trace timing**: `get_stack_trace()` is ~20ms on paused threads but ~600ms on running threads. The code avoids calling it on running threads unless necessary.

## Tests

This project uses `pytest` with `asyncio_mode = auto` (see `pytest.ini`), so all test functions are plain `async def` — no `@pytest.mark.asyncio` decorator needed.

### Test Structure

- Test files live in `tests/` and follow the naming convention `test_<tool_name>.py` (e.g., `test_set_breakpoint.py`).
- Each test is an `async def` function that takes the `client: Client` fixture (from `conftest.py`) as its first argument.
- Tests call MCP tools via `await client.call_tool("tool_name", {...})` and assert on `result.structured_content`.
- Read `tests.utils` before writing tests, it's short and you should use the functions in there to avoid repeating boilerplate.

### Fixtures

- `client` — async fixture providing a `fastmcp.Client` connected to the local MCP server. Always inject it as a parameter.
- `_cleanup_test_processes` — autouse session-scoped fixture that kills orphaned debugee processes at teardown.

### Assertions

- Assert the **full** `structured_content` dict against an expected dict using `assert result.structured_content == {...}`.
- For values that are inherently unpredictable (PIDs, ports, UUIDs), use `MatchAny(type)` from `tests.utils` inside the expected dict — it implements `__eq__` to match any instance of the given type.
- For string values with variable parts (paths, ports), use `MatchRegex(r"pattern")` from `tests.utils` — it implements `__eq__` to match strings against a regex.
- For error/negative cases, use `pytest.raises(ToolError, match=r"regex pattern")` with a raw-string regex.

### Fake Modules

- `tests/fakes/` contains simple Python scripts (`fake_main.py`, `fake_main_multi_thread.py`, etc.) that act as debugees.
- Fakes use `print(..., flush=True)` so stdout is immediately visible. Tests verify behavior by checking `std_out_path` content via `Path(...).read_text()`.
- Add new fakes when a test scenario requires specific code patterns (imports, threads, loops).
- Fake module paths are imported from `tests.constants`, and are relative paths computed from the fake module's `__file__`.

### Test Constants

- `PROJECT_ROOT` is computed as `Path(__file__).parent.parent.resolve()` — use it to build absolute paths in assertions.

### Process Verification

- Use `psutil.Process(pid)` to check debugee process state: `proc.is_running()`, `proc.cmdline()`, `proc.cwd()`, `proc.environ()`, `proc.status()`.
- Use `MatchRegex()` in `proc.cmdline()` assertions to handle symlink variations in the Python executable path.
- Use `await asyncio.sleep(1)` when a race condition exists between an action and its observable effect (e.g., after `resume` before checking threads).

### Parametrization

- Use `@pytest.mark.parametrize` for testing multiple variants of the same scenario (e.g., different file path formats).

### Multi-Step Workflows

- Tests often chain multiple tool calls to verify a complete workflow (e.g., create session → set breakpoint → wait_for_pause → list_threads → resume → verify completion).
- Reuse intermediate results (session IDs, PIDs, paths) across chained calls within a single test function.
