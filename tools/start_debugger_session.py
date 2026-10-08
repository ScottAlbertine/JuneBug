from typing import Annotated, Any

from annotations import ProjectPath


def start_debugger_session(
    configurationName: Annotated[str | None, "Name of the existing run configuration to debug."] = None,
    filePath: Annotated[
        str | None,
        "File path relative to the project root. Provide together with `line` to start debugging from a code location."
    ] = None,
    line: Annotated[
        int | None,
        "1-based line number for `filePath`. "
        "Provide together with `filePath` and do not combine with `configurationName`."
    ] = None,
    timeout: Annotated[int, "Timeout in milliseconds to wait for the debug session to start. Default: 60000."] = 60000,
    graceWaitMs: Annotated[
        int, "Grace wait in milliseconds after session starts to refresh state. Default: 2000."
    ] = 2000,
    programArguments: Annotated[
        str | None,
        "Optional program arguments override for this launch only. "
        "Pass this only when the selected run configuration reports `supportsDynamicLaunchOverrides=true` in `get_run_configurations`. "
        "Missing/null or empty string keeps the existing value; whitespace-only string clears it."
    ] = None,
    workingDirectory: Annotated[
        str | None,
        "Optional working directory override for this launch only. "
        "Pass this only when the selected run configuration reports `supportsDynamicLaunchOverrides=true` in `get_run_configurations`. "
        "Missing/null or empty string keeps the existing value; whitespace-only string clears it."
    ] = None,
    envs: Annotated[
        dict[str, str] | None,
        "Optional environment variable overrides for this launch only. "
        "Pass this only when the selected run configuration reports `supportsDynamicLaunchOverrides=true` in `get_run_configurations`. "
        "Missing/null keeps existing env unchanged; when provided, values are merged over existing env."
    ] = None,
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'sessionId': {
    #       'type': 'string',
    #       'description': 'Session identifier to use as `sessionId` in subsequent debugger calls. Uses session name by default; if duplicate names exist, format is `<sessionName>#<executionId>`.'
    #     },
    #     'name': {
    #       'type': 'string',
    #       'description': 'Human-readable session name.'
    #     },
    #     'state': {
    #       'type': 'string',
    #       'enum': [
    #         'running',
    #         'paused',
    #         'stopped'
    #       ],
    #       'description': 'Current session state.'
    #     },
    #     'runConfigurationName': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Associated run configuration name, if available.'
    #     },
    #     'breakpointsMuted': {
    #       'type': 'boolean',
    #       'description': 'Whether breakpoints are globally muted for this debugger session.'
    #     },
    #     'exitCode': {
    #       'type': [
    #         'integer',
    #         'null'
    #       ],
    #       'description': 'Process exit code. Absent when the tool returns before observing process termination, for example when the debuggee continues running after the session starts.'
    #     },
    #     'output': {
    #       'type': 'string',
    #       'description': 'Captured process output snapshot. When additional output exists, `<truncated>` is appended to the preview.'
    #     },
    #     'fullOutputPath': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Path to a temp file containing the full raw output. The file may continue growing while the process is still running and remains available while the IDE is running.'
    #     }
    #   },
    #   'required': [
    #     'sessionId',
    #     'name',
    #     'state',
    #     'output'
    #   ],
    #   'type': 'object'
    # }
    """Start a debugger session for either an existing run configuration by name or a code location
(`filePath` + `line`) in the current project.
Use this tool to start a debugger session.
Use this tool with either an existing run configuration name, or with `filePath` + `line`.
When using `filePath` + `line`, a line with a runnable method such as `main`, a test, or another executable
entry point will almost always work. If you are unsure which line to use, `get_run_configurations`
can help discover runnable locations in the file.
The session will be started and you can then use other debugger tools to control execution.

Preconditions:
- When using `configurationName`, pass the exact existing run configuration name; do not pass a test method name or other derived target identifier.
- When using `filePath` + `line`, point at a runnable code location such as `main`, a test, or another executable entry point.
- Set at least one breakpoint first; otherwise the program may run to completion without pausing.
- Pass either `configurationName`, or `filePath` together with `line`. These modes are mutually exclusive.

Behavior:
- Waits for session creation up to `timeout`.
- Applies a grace wait (`graceWaitMs`) after the session starts and returns refreshed state.
- Optional launch overrides (`programArguments`, `workingDirectory`, `envs`) are applied only for this debug launch and are not persisted.
- `get_run_configurations` is the source of truth for override support: only pass launch overrides when the selected run configuration reports `supportsDynamicLaunchOverrides=true`.
- Do not pass these override parameters unless you explicitly need to change the configured launch values for this debug launch.
- Missing/null override parameters keep existing run configuration values unchanged.
- For string overrides (`programArguments`, `workingDirectory`), missing/null or empty string (`""`) keeps the existing value unchanged.
- Pass a whitespace-only string such as `" "` to clear an existing value for this debug launch.

Next call:
- `control_session(action=WAIT_FOR_PAUSE)` to wait for first suspension.
- After pause, call `get_stack` and `get_frame_values` (or `evaluate_expression`) for runtime evidence.

Returns a flat result with debugger session metadata plus the execution snapshot fields from the launch:
- `sessionId`, `name`, `status`, and optional `runConfigurationName`
- `output` preview and optional `fullOutputPath`
- optional `exitCode` when process termination is already known"""

    if envs is None:
        envs = {}

    print(configurationName)
    print(filePath)
    print(line)
    print(timeout)
    print(graceWaitMs)
    print(programArguments)
    print(workingDirectory)
    print(envs)
    print(projectPath)

