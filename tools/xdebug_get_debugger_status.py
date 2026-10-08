from typing import Annotated, Any

from annotations import ProjectPath


def xdebug_get_debugger_status(projectPath: ProjectPath = None) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'sessions': {
    #       'type': 'array',
    #       'items': {
    #         'type': 'object',
    #         'required': [
    #           'id',
    #           'name',
    #           'state'
    #         ],
    #         'properties': {
    #           'id': {
    #             'type': 'string',
    #             'description': 'Session identifier to use as `sessionId` in debugger calls. Uses session name by default; if duplicate names exist, format is `<sessionName>#<executionId>`.'
    #           },
    #           'name': {
    #             'type': 'string',
    #             'description': 'Session display name.'
    #           },
    #           'state': {
    #             'type': 'string',
    #             'enum': [
    #               'running',
    #               'paused',
    #               'stopped'
    #             ],
    #             'description': 'Current session state.'
    #           },
    #           'runConfigurationName': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Associated run configuration name when available.'
    #           },
    #           'breakpointsMuted': {
    #             'type': 'boolean',
    #             'description': 'Whether breakpoints are globally muted for this debugger session.'
    #           },
    #           'currentPosition': {
    #             'type': [
    #               'object',
    #               'null'
    #             ],
    #             'required': [
    #               'filePath',
    #               'line'
    #             ],
    #             'properties': {
    #               'filePath': {
    #                 'type': 'string',
    #                 'description': 'File path as provided by the debugger (usually VirtualFile.url).'
    #               },
    #               'line': {
    #                 'type': 'integer',
    #                 'description': '1-based line number.'
    #               },
    #               'column': {
    #                 'type': [
    #                   'integer',
    #                   'null'
    #                 ],
    #                 'description': '1-based column number when available.'
    #               }
    #             },
    #             'description': 'Current source position for paused sessions, if available.'
    #           }
    #         }
    #       },
    #       'description': 'All currently known debug sessions.'
    #     },
    #     'activeSessionId': {
    #       'type': [
    #         'string',
    #         'null'
    #       ],
    #       'description': 'Identifier of the active session, if any.'
    #     }
    #   },
    #   'required': [
    #     'sessions'
    #   ],
    #   'type': 'object'
    # }
    """Returns the current status of the debugger including all active debug sessions.
Use this tool to get an overview of all running debug sessions and their states.

Preconditions:
- None.

Returns explicit `sessions[]` and `activeSessionId`.

Next call:
- If no sessions are running, call `xdebug_start_debugger_session`.
- If multiple sessions are active, use returned `id` as `sessionId` in subsequent calls."""
    print(projectPath)

