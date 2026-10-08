from typing import Annotated, Any

from annotations import ProjectPath, SessionID


def xdebug_run_to_line(
    filePath: Annotated[
        str,
        "Target source file path. Path to the file. "
        "Supports project-relative paths, paths with '..', absolute paths, archive entries like '/path/lib.jar!/pkg/Foo.class', "
        "and URLs such as 'file://', 'jar://', and 'jrt://'. "
        "Any path returned from the other tools can be passed as is (e.g. paths from 'search_*' tools)."
    ],
    line: Annotated[int, "Target line number (1-based)."],
    sessionId: SessionID = None,
    timeout: Annotated[int, "Timeout in milliseconds waiting for paused/stopped result. Default: 30000."] = 30000,
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'sessionId': {
    #       'type': 'string',
    #       'description': 'Session identifier.'
    #     },
    #     'outcome': {
    #       'type': 'string',
    #       'enum': [
    #         'paused',
    #         'stopped',
    #         'timeout'
    #       ],
    #       'description': 'Outcome after attempting run-to-line (paused/stopped/timeout).'
    #     },
    #     'currentPosition': {
    #       'type': [
    #         'object',
    #         'null'
    #       ],
    #       'required': [
    #         'filePath',
    #         'line'
    #       ],
    #       'properties': {
    #         'filePath': {
    #           'type': 'string',
    #           'description': 'File path as provided by the debugger (usually VirtualFile.url).'
    #         },
    #         'line': {
    #           'type': 'integer',
    #           'description': '1-based line number.'
    #         },
    #         'column': {
    #           'type': [
    #             'integer',
    #             'null'
    #           ],
    #           'description': '1-based column number when available.'
    #         }
    #       },
    #       'description': 'Current position when outcome is paused and position is known.'
    #     },
    #     'message': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Additional context message (timeout or errors).'
    #     }
    #   },
    #   'required': [
    #     'sessionId',
    #     'outcome'
    #   ],
    #   'type': 'object'
    # }
    """Resumes execution to a target line.
Use this tool to run until a specific source position without manually stepping.

Preconditions:
- Session must be suspended.
- Target file/line must be valid.

Outcome:
- paused: session paused at or after target.
- stopped: session terminated before pause.
- timeout: no pause/stop within timeout window.

Next call:
- If paused, call `xdebug_get_stack` / `xdebug_get_frame_values` / `xdebug_evaluate_expression`.
- If the session stopped or disappeared, refresh `sessionId` via `xdebug_get_debugger_status` before issuing another session-scoped call."""
    print(sessionId)
    print(filePath)
    print(line)
    print(timeout)
    print(projectPath)

