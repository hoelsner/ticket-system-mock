# Issue Lifecycle And Attachments

## Purpose

This guide gives contributors the implementation-oriented rules behind the
issue lifecycle, attachment handling, comment mentions, and audit behavior.

## Lifecycle Model

Use `workflow_state` as the one authoritative lifecycle field for an `Issue`.

At creation time, `category` is optional. Intake flows may persist an `Issue`
without a category and defer classification until triage.

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
```

`REJECTED` is the only exceptional workflow state. It is used when an `Issue`
should not continue through the normal lifecycle.

State changes should be recorded as `Issue State Transition` records.

## Description Templates

The HTML issue create page may offer a predefined `Issue Description`
template before the `Issue` is saved.

Implementation rules:

- templates are managed as admin-maintained reference data
- a template may be scoped to one `Collection`, one `Issue Category`, or both
- the create form should show the selector only when at least one active
  template is available
- selecting a template replaces the current description draft in the form
- the user may edit the inserted markdown before the issue is created
- the persisted `Issue Description` stores only the final edited markdown, not
  a reference back to the template

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

Attachments may enter the system through the user frontend or through the REST
API mutation flows for issue creation, issue update, and issue comments.

Those API flows should accept multipart form uploads so integrations can submit
files without bypassing the same validation and controller rules used by the
HTML forms.

### Create Form Staging

The HTML issue create page allows uploads before the `Issue` exists.

To keep the rule that a persisted attachment belongs to exactly one `Issue`,
the create flow stores uploads temporarily as `Draft Issue Attachment` records.

The staged record must keep the draft token, file metadata, and uploading
`User` so markdown preview and attachment suggestions can resolve the temporary
reference during form editing.

When the issue is created successfully:

- each staged file is materialized as an `Issue Attachment`
- draft attachment tokens in the markdown description are rewritten to the
  final attachment references
- the staged records are removed

If issue creation fails, the staged uploads remain tied to the draft token so
the user can continue editing without uploading the same files again.

## Attachment Embedding

An attached file can be embedded at a specific point inside the markdown
`Issue Description`.

Embedding means the issue description contains a stable reference to the
attachment while the attachment remains a separate persisted entity.

Example markdown syntax:

```markdown
Please review the attached log output:

{{ attachment:42 }}

The error appears after the interface reset.
```

The embedded attachment reference should point to an existing issue attachment.

During issue creation only, the editor may temporarily use a draft reference in
the form `{{ attachment:draft-<id> }}` until the final issue is saved.

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