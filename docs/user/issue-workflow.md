# Issue Workflow

## Purpose

This guide explains how an `Issue` moves through Ticket System Mock from
creation to completion. It is intended for users who need to
understand the product workflow and the main actions available during issue
handling.

## Overview

An `Issue` is created with a short title and a larger markdown-backed `Issue
Description`.

The issue lifecycle is controlled by one authoritative `Workflow State`.

## Workflow States

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

## Main Workflow

1. `Issue Creation`

   A user or integration system creates an `Issue` with a title and markdown
   `Issue Description`.

   The issue starts in the `NEW` workflow state.

   The creator may also attach supporting files such as screenshots, logs, or
   documents.

2. `Triage`

   A `User` reviews the new issue and classifies it.

   During triage, the `User` may assign an `Issue Category`, set the
   `Priority`, mark the issue as escalated, add an `Issue Comment`, or review
   attached files.

   The issue moves to `TRIAGE`.

3. `Group Dispatch`

   The issue is associated with one responsible `Group`.

   Once the issue has a responsible group, it can move to `ASSIGNED`.

4. `User Takes the Issue`

   A `User` from the assigned `Group` takes ownership of the issue.

   The issue is now associated with that `User` and moves to `IN_PROGRESS`.

5. `Issue Processing`

   The assigned `User` works on the issue.

   The `User` may add internal or customer-visible `Issue Comments`, upload
   additional attachments, and mention other users with `@username` references
   inside comments.

6. `Delegation or Waiting`

   If another `User` needs to continue the work, the current `User` can
   delegate the issue to another `User` from the responsible `Group`.

   If external input is required, the issue can move to `WAITING`.

7. `Resolution`

   When the work is complete, the `User` moves the issue to `RESOLVED`.

   The issue keeps its comments, mentions, transition history, assignments, and
   attachments.

8. `Closure`

   After review or confirmation, the issue moves to `CLOSED`.

   Closed issues remain available for reporting, audit, and demo workflows.

## Main User Views

- The `Instance Kanban Board` shows issues grouped by `Workflow State`.
- The `Personal Dashboard` shows issues assigned to one `User` and comments
   where that same `User` was mentioned.
- The `Issue Detail View` shows the full issue title, markdown description,
  comments, and attachments.

The `Instance Kanban Board` supports search and filtering in its standard view.
For presentations or wallboard-style monitoring, it can also be opened in a
fullscreen mode that hides the global top navigation, the visible board title,
and the search and filter controls.

## Attachments

Files can be attached to an `Issue` as supporting material.

Attachments may represent screenshots, logs, documents, exports, configuration
files, or other evidence relevant to the issue.

An attachment can also be referenced from the markdown `Issue Description` so
the description can point to the relevant file at a specific position.

## Related Documentation

- See [product-overview.md](product-overview.md) for the broader product scope
  and interface structure.
- See [../development/issue-lifecycle-and-attachments.md](../development/issue-lifecycle-and-attachments.md)
  for contributor-facing lifecycle, attachment, and audit rules.