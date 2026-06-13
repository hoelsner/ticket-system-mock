# n8n Node Reference

## Purpose

This reference describes each bundled n8n node in user-facing terms.
Use it when you already installed the package and need to understand which
node to choose, which operations it supports, and which fields matter most in a
workflow.

## Table of Contents

- [Shared credential](#shared-credential)
- [TSM - Reference Data](#tsm---reference-data)
- [TSM - Collection](#tsm---collection)
- [TSM - Category](#tsm---category)
- [TSM - Issue](#tsm---issue)
- [TSM - Issue Attachment](#tsm---issue-attachment)
- [TSM - Issue Activity](#tsm---issue-activity)
- [TSM - Issue Poll Trigger](#tsm---issue-poll-trigger)
- [TSM - Issue Webhook Trigger](#tsm---issue-webhook-trigger)
- [Node selection summary](#node-selection-summary)

## Shared Credential

All bundled nodes use the same `Ticket System Mock API` credential.

Configure these fields once in n8n:

- Base URL: the root URL of the web application, for example `https://example.local`
- Username: a valid application user name
- Password: the password for that user

The `Base URL` must be a full absolute URL.
Use `http://webapp:8000` inside the local Docker development stack.

Before building a larger workflow, test the credential with a simple read node
such as `TSM - Reference Data` using the `Health` operation.

If credential setup fails at runtime, the nodes now report clearer causes for
common problems such as:

- invalid or incomplete Base URLs
- unreachable hosts or refused connections
- `401 Unauthorized` credential failures
- `403 Forbidden` permission failures
- server-side API errors that include response detail text

## TSM - Reference Data

Use this node when a workflow needs lookup data or a lightweight API check.

### Main use cases

- confirm that the REST API is reachable
- resolve the authenticated user and profile
- list groups before assigning an Issue
- list users before assigning an Issue

### Supported operations

| Operation | Purpose |
| --- | --- |
| `Health` | Confirm that the API is reachable and authenticated correctly. |
| `Get Authenticated User` | Return the user behind the current API credential. |
| `Get My Profile` | Return the current user's profile information. |
| `Get User Profile` | Return the public profile for one user by username. |
| `List Groups` | Return dispatchable groups from the REST API list response. |
| `List Users` | Return active users, optionally filtered by one group, from the REST API list response. |

### Important inputs

- `Username` is required for `Get User Profile`.
- `Group ID` is optional for `List Users`. Use `0` to return all users.
- The underlying REST API wraps list results under a root `data` key. The node
  unwraps that list before passing the response to the workflow.
- Deactivated users are excluded from `List Users`, which keeps lookup results
  aligned with assignable accounts in the application.

### Typical workflow pattern

Use this node before a create or update step when the workflow should resolve
group and user IDs dynamically instead of hard-coding them.

## TSM - Collection

Use this node for collection reference data.

### Main use cases

- list active collections
- create a new collection
- update an existing collection

### Supported operations

| Operation | Purpose |
| --- | --- |
| `List` | Return active collections from the REST API list response. |
| `Create` | Create a new collection. |
| `Update` | Update one collection by ID. |

### Important inputs

- `Collection ID` is required for `Update`.
- `Name` and `Prefix` are required for create and update.
- `Next Issue Sequence` controls the next local sequence value used inside the collection.
- The underlying REST API wraps list results under a root `data` key. The node
  unwraps that list before passing the response to the workflow.

Use this node when the workflow needs to manage Issue numbering scopes or load
valid collection IDs before Issue creation.

## TSM - Category

Use this node for Issue category reference data.

### Main use cases

- list active Issue categories
- create a new Issue category
- update an existing Issue category

### Supported operations

| Operation | Purpose |
| --- | --- |
| `List` | Return active Issue categories from the REST API list response. |
| `Create` | Create a new Issue category. |
| `Update` | Update one Issue category by ID. |

### Important inputs

- `Category ID` is required for `Update`.
- `Name` and `Code` are required for create and update.
- `Is Active` controls whether the category remains available for new Issues.
- The underlying REST API wraps list results under a root `data` key. The node
  unwraps that list before passing the response to the workflow.

Use this node when the workflow needs valid category IDs or when automation
should maintain category metadata directly.

## TSM - Issue

Use this node for the main Issue lifecycle operations.

### Main use cases

- list matching Issues
- fetch full Issue detail
- create a new Issue
- update selected fields on an existing Issue
- archive an Issue
- move an Issue to another workflow state and board position

### Supported operations

| Operation | Purpose |
| --- | --- |
| `List` | Return Issues that match the supplied filters from the REST API list response. |
| `Get` | Return one Issue with comments, attachments, history, and transitions. |
| `Create` | Create a new Issue. |
| `Update` | Apply a sparse `PUT` update to one existing Issue. |
| `Archive` | Archive one Issue so it leaves active views. |
| `Move` | Move one Issue to a target workflow state and board position. |

### List operation

The `List` operation currently supports these filters:

- `Search`
- `Assignee`
- `Priority`
- `Collection`
- `Category`
- `Workflow State`
- `Workflow State Label`

`Priority` and `Workflow State` are select fields in the n8n node UI. Use the
`Any` option when that filter should be omitted.

The available `Workflow State` values match the current application workflow,
including `REJECTED` as the only exceptional state.

The underlying REST API wraps matching Issue summaries under a root `data` key.
The node unwraps that list before passing the response to the workflow.

Use `Workflow State` when you know the stored code, for example
`IN_PROGRESS`. Use `Workflow State Label` when you want to filter by the human
label, for example `In Progress`.

### Create operation

The `Create` operation accepts the main Issue fields:

- title
- markdown description
- collection ID
- category ID
- priority
- optional group ID
- optional user ID
- escalation flag
- workflow state

Use `Group ID = 0` or `User ID = 0` when no group or assignee should be stored.

### Update operation

The `Update` operation uses the `Update Fields` collection.
Only the fields you explicitly add are sent to the API.

That means you can:

- change only the title
- reassign only the group or user
- toggle only the escalation flag
- move the workflow state with a transition reason
- clear the group or user by setting the value to `0`

This is a sparse `PUT` pattern, not a full object replacement.
Omitted fields remain unchanged on the Issue.

### Archive operation

Set `Confirm Archive` to `true` to archive the Issue.
This is a soft-delete style action. The Issue leaves active views but its
history remains stored.

### Move operation

Use `Move` when the workflow should reposition an Issue on the board without
performing a broader field update.

Important fields:

- `Target State`
- `Position Index`

## TSM - Issue Attachment

Use this node for attachment-specific work on one Issue.

### Main use cases

- upload a new attachment to an Issue
- update the stored description of an attachment
- replace the file content of an existing attachment
- delete an attachment from an Issue

### Supported operations

| Operation | Purpose |
| --- | --- |
| `Add` | Upload a new attachment to an Issue. |
| `Update` | Update one attachment description and optionally replace its file content. |
| `Delete` | Delete one attachment from an Issue. |

### Add operation

Required inputs:

- `Issue ID`
- `Binary Property`

Optional input:

- `Description`

The `Binary Property` must match the incoming n8n binary property name, such as
`data`.

### Update operation

Required inputs:

- `Issue ID`
- `Attachment ID`

Optional inputs:

- `Description`
- `Replace File`
- `Replacement Binary Property`

If `Replace File` is `false`, the node only updates metadata such as the
description.

If `Replace File` is `true`, set `Replacement Binary Property` to the exact
incoming binary property name that contains the replacement file.

Example:

- a previous node outputs the file as `$binary.replacement`
- set `Replacement Binary Property` to `replacement`

If the property name does not exist on the input item, the node fails because
it cannot upload the replacement file.

### Delete operation

Required inputs:

- `Issue ID`
- `Attachment ID`

Use this when the workflow should remove an attachment entirely rather than just
replace or relabel it.

## TSM - Issue Activity

Use this node for Issue comments and, when needed, compatibility access to the
older attachment actions.

### Main use cases

- add a comment to an Issue
- update a comment body or visibility
- upload an attachment together with a new comment
- keep older workflows working if they still use attachment actions here

### Supported operations

| Operation | Purpose |
| --- | --- |
| `Add Comment` | Create a new comment on an Issue. |
| `Update Comment` | Update one existing comment. |
| `Add Attachment` | Add an attachment directly from this node. |
| `Update Attachment` | Update an attachment directly from this node. |
| `Delete Attachment` | Delete an attachment directly from this node. |

### Comment operations

`Add Comment` requires:

- `Issue ID`
- `Body`
- `Visibility`

Optional add-comment inputs:

- `Attachment Description`
- `Attachment Binary Property`

This lets one workflow step add a comment and upload one attachment in the same
request.

`Update Comment` requires:

- `Issue ID`
- `Comment ID`
- `Body`
- `Visibility`

### Attachment operations in this node

These operations still work, but new workflows should prefer
`TSM - Issue Attachment` because it keeps all attachment actions grouped in one
place.

Use `TSM - Issue Activity` mainly when the workflow is comment-focused and the
attachment belongs directly to that comment creation step.

## TSM - Issue Poll Trigger

Use this trigger when n8n should periodically look for changed Issues.

### Main use cases

- check for new or changed Issues on a schedule
- limit polling to a subset of Issues
- emit either Issue summaries or full Issue detail

### Available filters

- `Search`
- `Assignee`
- `Priority`
- `Collection`
- `Category`
- `Workflow State`
- `Workflow State Label`

`Priority` and `Workflow State` are select fields in the trigger UI. Use the
blank `Any` entry when the poller should not limit results by that filter.

### Important behavior

- `Load Full Issue Detail` makes the trigger call `/api/issues/{id}` for each
  matching changed Issue before emitting it.
- `Emit Existing Issues On First Poll` controls the initial run behavior.

If `Emit Existing Issues On First Poll` is enabled, the first poll emits the
currently matching Issues and sets the watermark.

If it is disabled, the first poll only records the watermark and later polls
emit newly changed Issues.

The trigger is delta-based after the initial watermark is established. It does
not emit unchanged Issues again on every poll.

## TSM - Issue Webhook Trigger

Use this trigger when the application already sends outbound webhooks to n8n.

### Main use cases

- react to Issue changes without polling
- filter inbound webhook deliveries by event type
- pass the webhook payload into downstream automation immediately

### Important inputs

- `Webhook Path`
- `Accepted Event Types`

### Supported event types

- `issue.created`
- `issue.updated`
- `issue.queue_assigned`
- `issue.commented`
- `issue.closed`

### Important behavior

This node receives deliveries only. It does not register itself in the web
application.

That means:

- you must configure the webhook endpoint in the application separately
- the application must be able to reach the n8n webhook URL
- the node emits `webhook_metadata` together with the received payload
- the received JSON body uses root `event` and `data` fields
- `webhook_metadata` mirrors the effective event under `webhook_metadata.event`

## Node Selection Summary

Use these rules when choosing between the nodes:

- use `TSM - Reference Data` for health, identity, group, and user lookups
- use `TSM - Collection` for collection reference data
- use `TSM - Category` for Issue category reference data
- use `TSM - Issue` for the main Issue lifecycle
- use `TSM - Issue Attachment` for dedicated attachment work
- use `TSM - Issue Activity` for comments and comment-plus-attachment patterns
- use `TSM - Issue Poll Trigger` when periodic detection is acceptable
- use `TSM - Issue Webhook Trigger` when the application can push events into n8n