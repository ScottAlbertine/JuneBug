# JuneBug — Agent Notes

## Python Toolchain

This is a `direnv` project (`.envrc` uses `layout python3`). The Python virtual environment lives at `.direnv/python-3.14/`.

## Tests

This project uses `pytest` with `asyncio_mode = auto` (see `pytest.ini`), so all test functions are plain `async def` — no `@pytest.mark.asyncio` decorator needed.

### Test Structure

- Test files live in `tests/` and follow the naming convention `test_<tool_name>.py` (e.g., `test_set_breakpoint.py`).
- Each test is an `async def` function that takes the `client: Client` fixture (from `conftest.py`) as its first argument.
- Tests call MCP tools via `await client.call_tool("tool_name", {...})` and assert on `result.structured_content`.
- Use the `create_session(client, file_path=...)` helper from `tests.utils` to start a debugger session — don't repeat the `start_debugger_session` boilerplate inline.

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
- Use `sleep(1)` (from `time`) when a race condition exists between an action and its observable effect (e.g., after `resume` before checking threads).

### Parametrization

- Use `@pytest.mark.parametrize` for testing multiple variants of the same scenario (e.g., different file path formats).

### Multi-Step Workflows

- Tests often chain multiple tool calls to verify a complete workflow (e.g., create session → set breakpoint → wait_for_pause → list_threads → resume → verify completion).
- Reuse intermediate results (session IDs, PIDs, paths) across chained calls within a single test function.
