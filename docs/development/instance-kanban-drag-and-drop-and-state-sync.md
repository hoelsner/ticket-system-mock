# Instance Kanban Board Drag And Drop With Backend State Synchronization

## Purpose

This document gives contributors a current-project implementation plan for drag
and drop on the `Instance Kanban Board`.

The board may use optimistic UI interactions, but the backend remains the
source of truth for `Workflow State`, Issue ordering, edit locks, and visual
 reconciliation.

## Table of Contents

- [Current Project Context](#current-project-context)
- [Implementation Intent](#implementation-intent)
- [Frontend Structure](#frontend-structure)
- [Backend Responsibilities](#backend-responsibilities)
- [Synchronization Rules](#synchronization-rules)
- [Edit Lock And Update Indicators](#edit-lock-and-update-indicators)
- [Acceptance Criteria](#acceptance-criteria)
- [Testing Guidance](#testing-guidance)
- [Follow-Up Work](#follow-up-work)

## Current Project Context

Use the current project terms and current board states when implementing this
feature.

- The primary work item is an `Issue`.
- The user-facing board is the `Instance Kanban Board`.
- The lifecycle field is `Workflow State`.
- Archived issues are not active board items.
- The current active board states are:
  - `NEW`
  - `TRIAGE`
  - `ASSIGNED`
  - `IN_PROGRESS`
  - `WAITING`
  - `RESOLVED`
  - `CLOSED`

The board is currently rendered from the user frontend route at `/`, and Issue
summaries are already represented through the reusable `Issue Card` component.

## Implementation Intent

Drag and drop should be treated as an interaction layer only.

- A dragged Issue may move optimistically in the DOM.
- The backend must validate and persist the requested move.
- The next backend event must reconcile the visible board to authoritative
  state.
- The frontend must never become the source of truth for `Workflow State`, card
  ordering, lock state, or edit-session status.

This feature should support two interaction types:

1. moving an `Issue` between workflow columns
2. reordering an `Issue` within the same workflow column

## Frontend Structure

Keep the implementation aligned with the current repository layout.

### Templates

Prefer extending the existing user frontend structure instead of creating a
parallel template tree.

- Keep the board route in the user frontend.
- Use the current board page in `src/webapp/templates/core/home.html` as the
  starting point.
- If the board markup becomes too large, split it into focused board fragments
  under `src/webapp/templates/core/kanban/`.
- Keep the reusable Issue summary in
  `src/webapp/templates/cotton/issue/card.html` or evolve that component into a
  board-capable Issue Card partial.

Recommended fragment split if the page grows:

- `src/webapp/templates/core/kanban/board.html`
- `src/webapp/templates/core/kanban/_column.html`
- `src/webapp/templates/core/kanban/_card.html`

### Data Attributes

Use stable data attributes so server-rendered fragments and JavaScript event
delegation can target board regions consistently.

- `data-kanban-board`
- `data-kanban-column`
- `data-workflow-state`
- `data-issue-id`
- `data-kanban-card`
- `data-edit-state`
- `data-edit-owner`
- `data-lock-state`
- `data-last-updated-at`
- `data-reconciliation-state`

### JavaScript

Keep drag and drop logic in a dedicated static asset.

Recommended file:

- `src/webapp/static/js/kanban-dnd.js`

Guidance:

- Use plain JavaScript.
- Keep templates presentation-focused.
- Do not place workflow mutation logic in templates.
- Do not create a client-side source of truth for board state.
- Use JavaScript only for short-lived drag state, placeholder management, move
  dispatch, and pending-reconciliation markers.

Expected behaviors:

- initialize drag-and-drop bindings from one entry point
- mark one Issue Card as the active dragged card
- create and move a placeholder while dragging
- dispatch a client event when a drop is requested
- send the move request to the backend
- mark the moved card or board as pending reconciliation
- clean up temporary drag state on `dragend`, `drop`, and guarded `dragleave`
- block dragging when an Issue is locked or actively edited by another user

### CSS

Keep board-specific styling inside the current shared user-frontend stylesheet
unless a dedicated board stylesheet becomes justified.

Current preferred file:

- `src/webapp/static/css/user-interface.css`

Required styling concerns:

- board layout
- column layout
- Issue Card placeholder
- dragged-card state
- pending-reconciliation state
- being-edited state
- locked state
- stale state
- recently-updated state

## Backend Responsibilities

The backend must own all persisted workflow and ordering decisions.

### Move Endpoint

Create or extend a backend endpoint that accepts move requests with:

- `issueId`
- `toWorkflowState`
- `newIndex`

The backend must:

- validate the Issue exists
- validate authorization
- validate the target `Workflow State`
- validate whether the transition is allowed
- validate whether the Issue is currently locked or being edited by another
  user
- persist the new state and order when valid
- reject the move when invalid
- emit an authoritative board update event after processing

### Ordering Model Requirement

Reordering inside a column requires persisted order, not only visual DOM order.

Before implementing drag-and-drop reordering, add or confirm a persisted board
ordering model for Issues within each active `Workflow State`.

### SSE Endpoint

Use a backend SSE endpoint for server-driven reconciliation, for example a board
event stream under the user frontend.

Each event should include:

- an event name
- enough target metadata to replace the correct board region
- a backend-rendered HTML fragment representing authoritative state

Suggested event types:

- `kanban.board.updated`
- `kanban.column.updated`
- `kanban.issue.updated`
- `kanban.issue.moved`
- `kanban.issue.editing.started`
- `kanban.issue.editing.heartbeat`
- `kanban.issue.editing.ended`
- `kanban.issue.locked`
- `kanban.issue.unlocked`
- `kanban.issue.stale`

Prefer the narrowest replacement that still keeps the board correct:

- replace the full board for coarse updates
- replace one column for movement updates
- replace one Issue Card for metadata, lock, or edit-state updates

## Synchronization Rules

The drag interaction may be optimistic, but reconciliation must always come
from backend events.

### Drag Start

When dragging starts:

- assign a temporary DOM identifier to the dragged card
- set the drag operation to `move`
- set a custom `DataTransfer` type such as `application/x-kanban-issue`
- add a visual dragged state
- block drag start if the Issue is locked or actively edited by another user

### Drag Over

When dragging over a valid column:

- accept the drag only when the custom Kanban type is present
- prevent default browser behavior only for valid drags
- calculate the intended insertion point from pointer position
- show a placeholder at the intended drop position

### Drop

When dropping:

1. move the Issue Card optimistically in the DOM
2. remove the placeholder
3. remove temporary drag state
4. update temporary visible state markers if needed
5. dispatch `kanban:issue-moved`
6. send the move request to the backend
7. mark the card or board as pending reconciliation
8. wait for the SSE update
9. replace the affected DOM region from backend-rendered HTML
10. clear the pending-reconciliation marker

If the backend rejects the move, the SSE update must restore the authoritative
board state.

## Edit Lock And Update Indicators

Manual editing through the `Issue Detail View` must be visible on the
`Instance Kanban Board`.

Each Issue Card may expose these states:

- normal
- pending reconciliation
- being edited
- locked
- stale
- recently updated

Use backend-driven state for these indicators.

When an edit session starts:

- the backend records the Issue, editing User, timestamps, and expiration
- the backend emits an SSE update for the affected Issue
- the Issue Card shows an editing indicator
- drag and drop is disabled or explicitly guarded for that Issue

When an edit session ends or expires:

- the backend clears the edit session
- the backend emits a new event
- the Issue Card removes the editing indicator
- the Issue becomes draggable again if no other lock exists

When an Issue is saved from the detail view:

- the backend persists the changed fields
- the backend emits an update event
- the Issue Card shows a temporary recently-updated state
- a later backend event or short client-side visual timeout may clear the
  highlight

## Acceptance Criteria

Implementation is complete when all of the following are true.

- The `Instance Kanban Board` renders all active workflow columns.
- Issue Cards appear in the correct initial columns.
- Issue Cards can be dragged between columns.
- Issue Cards can be reordered within one column.
- A placeholder shows the intended drop position.
- A dragged Issue Card is visually dimmed while dragging.
- Dropping an Issue Card dispatches `kanban:issue-moved`.
- Dropping an Issue Card sends a move request to the backend.
- Backend SSE updates reconcile the visible board without a full page reload.
- Rejected moves are corrected by backend state.
- Locked or actively edited Issues cannot be moved without backend approval.
- Manual detail-view edits appear on the board through backend-driven lock,
  stale, edit, or update indicators.
- Reloading the page shows the same state persisted by the backend.

## Testing Guidance

At least one relevant test should fail before implementation because drag and
drop, move persistence, SSE reconciliation, or edit-lock behavior does not yet
exist.

### Unit And View Tests

Add contributor-facing tests that verify:

- the board route returns HTTP 200
- all workflow columns are present
- Issue Cards include stable Issue identifiers
- Issue Cards expose drag-related attributes only when movable
- locked or edited Issues are guarded correctly
- the board includes the required JavaScript asset
- the board includes the SSE connection attributes when implemented

### Integration Tests

Add tests that verify:

- Issues are grouped by `Workflow State`
- empty columns render correctly
- Issue order is stable within each column
- the move endpoint persists valid moves
- invalid or conflicting moves are rejected
- rejected moves preserve backend state
- SSE events return valid `text/event-stream` responses
- edit-session changes emit the expected update events

### Browser-Level Verification

Add a documented live check or Playwright test for:

1. moving an Issue from one workflow column to another
2. reordering an Issue within a column
3. confirming `kanban:issue-moved` is emitted
4. confirming the backend persists or rejects the move
5. confirming the final DOM matches the SSE-reconciled backend state
6. opening an Issue in the detail view and confirming the edit indicator
7. confirming locked or edited Issues cannot be dragged successfully

## Follow-Up Work

Recommended follow-up items:

- add persisted board ordering for Issues if it does not already exist
- add authorization rules for workflow transitions initiated from the board
- add explicit user feedback for rejected moves
- add Playwright coverage for drag-and-drop behavior
- add Playwright coverage for edit-lock behavior
- add audit records for Issue movement and manual Issue edits
- add stale edit-session cleanup and expiration handling