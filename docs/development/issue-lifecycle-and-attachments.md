# Issue Lifecycle And Attachments

## Purpose

This guide gives contributors the implementation-oriented rules behind the
issue lifecycle, attachment handling, comment mentions, and audit behavior.

## Lifecycle Model

Use `workflow_state` as the one authoritative lifecycle field for an `Issue`.

```text
NEW
-> TRIAGE
-> ASSIGNED
-> IN_PROGRESS
-> WAITING
-> RESOLVED
-> CLOSED
```

Exceptional states:

```text
REJECTED
DUPLICATE
```

State changes should be recorded as `Issue State Transition` records.

## Attachments

An attachment belongs to exactly one `Issue`.

Suggested attachment metadata:

- original filename
- stored file reference
- content type
- file size
- uploaded by `User`
- uploaded timestamp
- optional description

## Attachment Embedding

An attached file can be embedded at a specific point inside the markdown
`Issue Description`.

Embedding means the issue description contains a stable reference to the
attachment while the attachment remains a separate persisted entity.

Example markdown syntax:

```markdown
Please review the attached log output:

{{ attachment:network-log-2026-06-04.txt }}

The error appears after the interface reset.
```

The embedded attachment reference should point to an existing issue attachment.

Do not store embedded file content directly in the issue description.

## Comment Mentions

Comments may include `@username` references.

These references should be extracted and persisted as `Comment Mention`
relations so the `Personal Dashboard` can be derived efficiently without
re-parsing every comment body.

## Derived Views

- The `Instance Kanban Board` is derived from issues grouped by `Workflow
  State`.
- The `Personal Dashboard` is derived from issues assigned to one `User` and
  `Comment Mention` records that reference that same `User`.

No separate persisted board or dashboard entity is required.

## Audit Behavior

Every lifecycle change should be stored as an `Issue State Transition`.

Each transition should record:

- the issue
- the previous workflow state
- the new workflow state
- the `User` who performed the change
- the timestamp
- an optional reason

Attachment uploads should also be auditable.

At minimum, the system should record:

- the issue
- the attachment
- the uploading `User`
- the upload timestamp

## Modeling Rules

- Use `Issue`, not ticket.
- Use `Workflow State`, not status or phase.
- Use `User` as the canonical term for the acting Django `User`, whether
  person or system.
- Use `Group` as the canonical term for the responsible Django `Group`.
- Keep the `Instance Kanban Board` and `Personal Dashboard` as derived read
  models.
- Model `Escalation` as a flag on the `Issue`, not as a workflow state.
- Store issue descriptions as markdown.
- Store file attachments as separate persisted entities.
- Allow markdown descriptions to reference attachments at specific positions.
- Store comment mentions as explicit relations.
- Store only stable attachment references in markdown.

## Related Documentation

- See [data-model.md](data-model.md) for the conceptual entity and relationship
  model.
- See [../user/issue-workflow.md](../user/issue-workflow.md) for the user-facing
  workflow description.