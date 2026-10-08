from typing import Annotated, Any

from annotations import ProjectPath, SessionID


def get_threads(
    sessionId: SessionID = None,
    limit: Annotated[int, "Page size. Default: 50, max: 200."] = 200,
    offset: Annotated[int, "Page offset. Default: 0."] = 0,
    projectPath: ProjectPath = None,
) -> dict[str, Any]:
    # {
    #   'properties': {
    #     'threads': {
    #       'type': 'array',
    #       'items': {
    #         'type': 'object',
    #         'required': [
    #           'id',
    #           'name',
    #           'state',
    #           'isCurrent'
    #         ],
    #         'properties': {
    #           'id': {
    #             'type': 'string',
    #             'description': 'Thread identifier to pass as `threadId` in `get_stack`.'
    #           },
    #           'name': {
    #             'type': 'string',
    #             'description': 'Human-readable thread name.'
    #           },
    #           'state': {
    #             'type': 'string',
    #             'description': 'Current thread status from debugger perspective.'
    #           },
    #           'isCurrent': {
    #             'type': 'boolean',
    #             'description': 'Whether this thread is currently selected.'
    #           },
    #           'additionalInfo': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Additional thread display info when available.'
    #           },
    #           'additionalInfoTooltip': {
    #             'type': [
    #               'string',
    #               'null'
    #             ],
    #             'description': 'Tooltip for additional thread display info when available.'
    #           },
    #           'frameCount': {
    #             'type': [
    #               'integer',
    #               'null'
    #             ],
    #             'description': 'Number of stack frames when available.'
    #           }
    #         }
    #       },
    #       'description': 'Threads available in the suspended debug session (paginated).'
    #     },
    #     'offset': {
    #       'type': 'integer',
    #       'description': 'Requested page offset.'
    #     },
    #     'limit': {
    #       'type': 'integer',
    #       'description': 'Requested page limit.'
    #     },
    #     'totalCount': {
    #       'type': 'integer',
    #       'description': 'Total known thread count.'
    #     }
    #   },
    #   'required': [
    #     'threads',
    #     'offset',
    #     'limit',
    #     'totalCount'
    #   ],
    #   'type': 'object'
    # }
    """Returns the list of threads in the debug session.
Use this tool to see all threads and their current status.

Preconditions:
- Session must be suspended.

Next call:
- Use `get_stack` for the selected thread.

Pagination:
- `offset`/`limit` are applied after collecting all stacks.

Ordering:
- Active thread first.
- Remaining threads are sorted by descending stack depth.

Schema fields: id, name, state, isCurrent, additionalInfo, additionalInfoTooltip, frameCount.
`additionalInfo`/`additionalInfoTooltip` use additional display info when available."""
    print(sessionId)
    print(limit)
    print(offset)
    print(projectPath)

