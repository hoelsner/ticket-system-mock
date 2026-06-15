# Ticket System Mock Python SDK

This package provides synchronous and asynchronous Python clients for the
Ticket System Mock REST API.

## Install

Create and sync the dedicated Python 3.14 virtual environment inside the SDK
directory:

```bash
cd src/ticketsystemmock
uv sync --python 3.14
```

The package depends on `httpx` and supports both sync and async clients.

When the web application image or development server exposes the SDK on the
authenticated Integrations page, you can also install the downloaded source
distribution directly into your own environment:

```bash
uv venv --python 3.14 .venv
. .venv/bin/activate
python -m pip install /path/to/ticketsystemmock-0.1.0.tar.gz
```

## Sync Example

```python
from ticketsystemmock import CommentVisibility, IssuePriority, TicketSystemClient, WorkflowState

with TicketSystemClient("http://webapp:8000", "admin", "admin1234") as client:
    current_user = client.auth.me()
    print(current_user.username)

    issues = client.issues.list(
        search="router",
        priority=IssuePriority.HIGH,
        workflow_state=WorkflowState.NEW,
    )

    created = client.issues.create(
        title="Investigate uplink packet loss",
        description_markdown="Packet loss started after the maintenance window.",
        collection=1,
        category=1,
        priority=IssuePriority.HIGH,
    )

    client.comments.add(
        created.issue.id,
        body="Initial triage completed.",
        visibility=CommentVisibility.INTERNAL,
    )
```

## Async Example

```python
from ticketsystemmock import AsyncTicketSystemClient, WorkflowState


async def main():
    async with AsyncTicketSystemClient("http://webapp:8000", "admin", "admin1234") as client:
        board = await client.board.get(workflow_state=WorkflowState.IN_PROGRESS)
        print(board.board_issue_count)
```

## Client Surface

The sync and async clients expose the same high-level resource layout:

- `client.system` for health checks
- `client.auth` for the authenticated user
- `client.profiles` for profile reads and updates
- `client.reference` for collections, categories, groups, and assignable users
- `client.board` and `client.dashboard` for read models
- `client.issues` for issue CRUD, move, and archive
- `client.comments` for comment add and update helpers
- `client.attachments` for attachment add, update, delete, and download helpers
- `client.admin.users` and `client.admin.groups` for superuser-only management endpoints
- `client.admin.workflow_state_auto_assignment_rules` for superuser-only workflow rule CRUD
- `client.admin.reset_instance(...)` for guarded superuser-only instance reset

## Notes

- The SDK mirrors the current REST API contract rather than hiding it behind a separate domain model.
- List endpoints that return `{"data": [...]}` on the wire are normalized into typed response models internally and usually exposed as entity lists at the public method layer.
- Attachment `file_url` values returned by the API are relative paths; use `IssueAttachment.resolved_file_url(...)` when you need an absolute download URL.
- Issue mutations use form-style payloads, and the SDK handles JSON versus multipart encoding based on the target endpoint.
- The guarded `reset_instance` operation preserves only the authenticated superuser account used for the request.