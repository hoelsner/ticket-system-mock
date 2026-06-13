# n8n Integration Guide

## Purpose

This guide explains how to use the bundled n8n nodes with the application.
It focuses on the operator workflow: download the package, place it in the
`n8n` custom node directory, configure credentials, and choose the right node
pattern for your automation.

## Table of Contents

- [When to use this guide](#when-to-use-this-guide)
- [What the n8n package provides](#what-the-n8n-package-provides)
- [Before you begin](#before-you-begin)
- [Download and stage the package](#download-and-stage-the-package)
- [Configure the API credential](#configure-the-api-credential)
- [Choose the right node](#choose-the-right-node)
- [Use the node reference](#use-the-node-reference)
- [Integration patterns](#integration-patterns)
- [Webhook trigger limitation](#webhook-trigger-limitation)
- [Example webhook events](#example-webhook-events)
- [Suggested first workflow](#suggested-first-workflow)
- [Troubleshooting](#troubleshooting)
- [Related documents](#related-documents)

## When to Use This Guide

Use this guide when you want to:

- connect an n8n instance to the application
- automate work against the application's REST API
- create or update an Issue from a workflow
- synchronize Issue data into another system
- react to Issue changes by polling or by receiving webhook deliveries

## What the n8n Package Provides

The bundled package contains separate nodes for the main integration tasks.

| Node | Main use |
| --- | --- |
| `TSM - Reference Data` | Read health, authenticated user, profile, group, and user data from the application. |
| `TSM - Collection` | List, create, and update collections. |
| `TSM - Category` | List, create, and update Issue categories. |
| `TSM - Issue` | List, read, create, update, archive, and move an Issue. |
| `TSM - Issue Attachment` | Add, update, or delete an Issue attachment. |
| `TSM - Issue Activity` | Add or update an Issue Comment and support older comment-plus-attachment patterns. |
| `TSM - Issue Poll Trigger` | Poll the application for Issue changes. |
| `TSM - Issue Webhook Trigger` | Receive outbound webhook deliveries sent by the application. |

## Before You Begin

Confirm the following prerequisites before installing the package:

- you can sign in to the web application
- your target environment exposes the REST API to the n8n instance
- you have a user account that is allowed to call the API
- you know the base URL for the application, for example `https://example.local`
- your n8n instance allows private or custom node installation

If you use the webhook trigger, also confirm that the application can reach the
n8n webhook URL over the network.

## Download and Stage the Package

The packaged node file is bundled with the deployed web application.

1. Sign in to the web application.
2. Open the `Integrations` page from the authenticated navigation.
3. Download the n8n node package file.
4. On the `n8n` host, create the custom node directory when needed:

  ```bash
  mkdir -p ~/.n8n/custom/node_modules/n8n-nodes-ticket-system-mock
  ```

5. Unpack the downloaded file into that directory:

  ```bash
  tar -xzf n8n-nodes-ticket-system-mock-*.tgz \
    -C ~/.n8n/custom/node_modules/n8n-nodes-ticket-system-mock \
    --strip-components=1
  ```

6. Restart or refresh `n8n` so the new package is loaded.

After extraction, the target directory should contain the package files such as
`package.json` and `dist/` under:

```text
~/.n8n/custom/node_modules/n8n-nodes-ticket-system-mock/
```

## Configure the API Credential

After the package is installed, create the shared API credential in n8n.

Configure these values:

- base URL: the root URL of the web application
- username: the application user name for API access
- password: the password for that user

The base URL must be a full absolute address that starts with `http://` or
`https://`.

Examples:

- `https://ticket-system.example.com`
- `http://webapp:8000` inside the local Docker development stack

Use a dedicated integration user when possible. This keeps workflow activity
separate from interactive user activity and makes audit behavior easier to
understand.

Before building production workflows, run a simple read operation such as a
health or profile request to confirm the credential works.

## Choose the Right Node

Use the node that matches the job you want n8n to perform.

- use `TSM - Reference Data` when a workflow needs lookup values or a basic API
  connectivity check for health, identity, group, and user data
- use `TSM - Collection` when a workflow needs to list or maintain collections
- use `TSM - Category` when a workflow needs to list or maintain Issue categories
- use `TSM - Issue` when a workflow needs to create, query, update, archive, or move
  an Issue
- use `TSM - Issue Attachment` when a workflow needs to add, replace, relabel, or
  delete an attachment on an Issue
- use `TSM - Issue Activity` when a workflow needs to add or update an Issue Comment,
  especially when the comment step should also upload one attachment
- use `TSM - Issue Poll Trigger` when n8n should periodically discover changed Issue
  records
- use `TSM - Issue Webhook Trigger` when the application is already configured to send
  webhook deliveries to n8n

## Use the Node Reference

Use this guide for installation and node selection.
Use the dedicated node reference for per-node detail:

- [n8n Node Reference](n8n-node-reference.md)

That reference documents the current operations, important inputs, and behavior
notes for each bundled node.

## Integration Patterns

### Create or update Issues from another system

Use action nodes when n8n is the orchestrator.

Typical pattern:

1. Receive input from email, a form, or another external system.
2. Map the incoming values to the application's Issue fields.
3. Use the `TSM - Issue` node to create or update the Issue.
4. Optionally use `TSM - Issue Activity` to add a follow-up Issue Comment.
5. Optionally use `TSM - Issue Attachment` to add or replace attachments as a
  separate step.

### Pass a replacement binary property into the attachment node

Use `TSM - Issue Attachment` when you need to replace the stored file content on
an existing attachment.

Typical pattern:

1. Use a previous node that outputs binary data, such as `Read Files From Disk`,
  `HTTP Request`, or another custom step.
2. Confirm the incoming binary property name, for example `data`, `attachment`,
  or `replacement`.
3. In `TSM - Issue Attachment`, choose `Update`.
4. Set `Replace File` to `true`.
5. Enter that exact incoming binary property name in `Replacement Binary Property`.

Example: if the previous node places the replacement file in
`$binary.replacement`, then set `Replacement Binary Property` to `replacement`.

If the binary property name does not match the actual input item, n8n returns an
error because the node cannot find the replacement file to upload.

### Read reference data before writing

Use the `TSM - Reference Data`, `TSM - Collection`, and `TSM - Category` nodes
before create or update steps when the workflow needs valid group, user,
collection, or category values.

This reduces avoidable validation failures caused by stale hard-coded IDs.

### React to Issue changes with polling

Use `TSM - Issue Poll Trigger` when the application cannot push events directly to
n8n or when polling is operationally simpler.

The poll trigger is useful when you want to:

- check for changed Issues on a schedule
- filter by search text, assignee, collection, category, and workflow state label
- choose `Priority` and `Workflow State` from built-in select lists instead of
  typing raw values manually
- optionally load the full Issue detail before continuing the workflow

The built-in `Workflow State` lists follow the current application workflow and
include `REJECTED` as the only exceptional state.

### React to Issue changes with webhooks

Use `TSM - Issue Webhook Trigger` when the application is configured to send webhook
events to an n8n endpoint.

This pattern gives lower latency than polling, but it depends on external
webhook configuration and network reachability between the application and n8n.

## Webhook Trigger Limitation

The current webhook trigger is a receive endpoint in n8n. It does not register
itself in the application.

That means:

- the trigger can receive webhook deliveries from the application
- the application must already be configured to send those deliveries to the
  n8n webhook URL
- webhook subscription management is currently a manual application-side step
- no webhook signature verification is documented for this node at this time

If you cannot configure outbound webhooks in the target environment yet, use
`TSM - Issue Poll Trigger` instead.

## Example Webhook Events

The Web Application delivers webhook events as HTTP `POST` requests with a JSON
body.

Typical headers look like this:

```text
Content-Type: application/json
X-Webhook-Event: issue.updated
X-Webhook-Event-Id: 6b5f34fe-3ecb-4b2d-8f93-c09f12a9d911
X-Webhook-Timestamp: 2026-06-13T09:14:27Z
X-Webhook-Signature: sha256=4d6f1d5c2e8a0b5d3b0f8f7f2f77f8b4f94e8a8f8b8a9d6b8c6d4e3f2a1b0c9d
```

The JSON body always includes these top-level fields:

- `base_url`
- `event_id`
- `event`
- `occurred_at`
- `actor`
- `data`

Depending on the event type, the payload can also include `changes`,
`transition`, or `comment`.

### Example: `issue.created`

Use this event when a new Issue was created.

```json
{
  "base_url": "https://tickets.example.local",
  "event_id": "6f6f4d4d-8f35-41a1-b7d0-12f86d3ef101",
  "event": "issue.created",
  "occurred_at": "2026-06-13T09:12:10Z",
  "actor": {
    "id": 7,
    "type": "user",
    "display_name": "alex.morgan"
  },
  "data": {
    "id": 42,
    "key": "TASK-42",
    "title": "VPN access request",
    "description": "User cannot connect to the corporate VPN.",
    "workflow_state": "NEW",
    "priority": "MEDIUM",
    "collection": {
      "id": 1,
      "name": "Operations Tasks",
      "prefix": "TASK"
    },
    "category": {
      "id": 3,
      "name": "Access Request",
      "code": "ACC"
    },
    "queue": null,
    "assigned_user": null,
    "is_escalated": false,
    "created_at": "2026-06-13T09:12:10Z",
    "updated_at": "2026-06-13T09:12:10Z",
    "resolved_at": null,
    "closed_at": null,
    "archived_at": null,
    "links": {
      "detail": "https://tickets.example.local/issues/42",
      "api": "https://tickets.example.local/api/issues/42"
    }
  }
}
```

### Example: `issue.updated`

Use this event when a tracked Issue field changed. The extra `changes` object
only contains the fields that actually changed.

```json
{
  "base_url": "https://tickets.example.local",
  "event_id": "f52ee7fd-84da-4fa9-b817-7069fcbdb4a4",
  "event": "issue.updated",
  "occurred_at": "2026-06-13T09:14:27Z",
  "actor": {
    "id": 11,
    "type": "user",
    "display_name": "sam.chen"
  },
  "data": {
    "id": 42,
    "key": "TASK-42",
    "title": "VPN access request",
    "description": "User cannot connect to the corporate VPN.",
    "workflow_state": "ASSIGNED",
    "priority": "HIGH",
    "collection": {
      "id": 1,
      "name": "Operations Tasks",
      "prefix": "TASK"
    },
    "category": {
      "id": 3,
      "name": "Access Request",
      "code": "ACC"
    },
    "queue": {
      "id": 4,
      "name": "Network Operations"
    },
    "assigned_user": {
      "id": 11,
      "username": "sam.chen",
      "display_name": "Sam Chen"
    },
    "is_escalated": true,
    "created_at": "2026-06-13T09:12:10Z",
    "updated_at": "2026-06-13T09:14:27Z",
    "resolved_at": null,
    "closed_at": null,
    "archived_at": null,
    "links": {
      "detail": "https://tickets.example.local/issues/42",
      "api": "https://tickets.example.local/api/issues/42"
    }
  },
  "changes": {
    "workflow_state": {
      "from": "NEW",
      "to": "ASSIGNED"
    },
    "priority": {
      "from": "MEDIUM",
      "to": "HIGH"
    },
    "queue": {
      "from": null,
      "to": {
        "id": 4,
        "name": "Network Operations"
      }
    },
    "assigned_user": {
      "from": null,
      "to": {
        "id": 11,
        "username": "sam.chen",
        "display_name": "Sam Chen"
      }
    },
    "is_escalated": {
      "from": false,
      "to": true
    }
  }
}
```

### Example: `issue.commented`

Use this event when a new Issue comment was added. The extra `comment` object
contains the emitted comment snapshot.

```json
{
  "base_url": "https://tickets.example.local",
  "event_id": "f31c81bf-f3cf-4d7b-8e80-d07c63dff0bb",
  "event": "issue.commented",
  "occurred_at": "2026-06-13T09:18:02Z",
  "actor": {
    "id": 11,
    "type": "user",
    "display_name": "Sam Chen"
  },
  "data": {
    "id": 42,
    "key": "TASK-42",
    "title": "VPN access request",
    "description": "User cannot connect to the corporate VPN.",
    "workflow_state": "ASSIGNED",
    "priority": "HIGH",
    "collection": {
      "id": 1,
      "name": "Operations Tasks",
      "prefix": "TASK"
    },
    "category": {
      "id": 3,
      "name": "Access Request",
      "code": "ACC"
    },
    "queue": {
      "id": 4,
      "name": "Network Operations"
    },
    "assigned_user": {
      "id": 11,
      "username": "sam.chen",
      "display_name": "Sam Chen"
    },
    "is_escalated": true,
    "created_at": "2026-06-13T09:12:10Z",
    "updated_at": "2026-06-13T09:18:02Z",
    "resolved_at": null,
    "closed_at": null,
    "archived_at": null,
    "links": {
      "detail": "https://tickets.example.local/issues/42",
      "api": "https://tickets.example.local/api/issues/42"
    }
  },
  "comment": {
    "id": 105,
    "type": "internal",
    "body": "Need network logs from the client device.",
    "visibility": "INTERNAL",
    "created_at": "2026-06-13T09:18:02Z",
    "author": {
      "id": 11,
      "type": "user",
      "display_name": "Sam Chen"
    }
  }
}
```

### Other supported event types

- `issue.queue_assigned` adds a `transition` object with `from_queue`,
  `to_queue`, `from_state`, and `to_state`.
- `issue.closed` sets the Issue `workflow_state` to `CLOSED` and can also
  include a `transition` object when the close operation created a workflow
  transition record.

For REST API consumers, the list endpoints at `/api/issues`, `/api/groups`,
`/api/users`, `/api/collections`, and `/api/categories` now return their
result arrays under the same root `data` key.

Treat these examples as shape references. Real ids, usernames, timestamps,
links, and field values depend on the current Issue and your environment.

## Suggested First Workflow

Start with a small validation workflow before building larger automations.

1. Add a manual or scheduled trigger in n8n.
2. Add a `TSM - Reference Data` node and confirm authentication works.
3. Optionally add `TSM - Collection` or `TSM - Category` if the workflow needs
  live reference IDs.
4. Add a `TSM - Issue` node that lists or creates an Issue.
5. Run the workflow and review the output mapping.
6. Only after that, add comments, attachments, or downstream system steps.

This sequence isolates credential and field-mapping problems early.

## Troubleshooting

If the integration does not work as expected, check these areas first:

- the n8n package was downloaded from the application's `Integrations` page
- the package files were unpacked under
  `~/.n8n/custom/node_modules/n8n-nodes-ticket-system-mock/`
- the n8n instance was restarted or refreshed if your deployment model needs
  that after custom-node installation
- the base URL points to the web application root and is reachable from n8n
- the integration user credentials are valid
- the target collection, category, group, or user values still exist
- the webhook URL is reachable from the application when using the webhook
  trigger
- the environment is configured for outbound webhooks if you expect push-based
  delivery

The bundled nodes now return more specific runtime messages for common setup
and permission problems.

Typical examples:

- if the Base URL is missing a scheme or is otherwise malformed, n8n reports
  that the Ticket System Mock API Base URL must be a valid `http://` or
  `https://` address
- if n8n cannot resolve or reach the target host, the node reports that the
  Ticket System Mock instance is not reachable from n8n
- if the username or password is wrong, the node reports `401 Unauthorized`
  and points you back to the credential configuration
- if the user can authenticate but cannot perform the requested action, the
  node reports `403 Forbidden` and explains that the configured user lacks
  permission for that operation
- if the application returns a server-side error, the node includes the API
  status code and any detail text returned by the server

If the webhook path is hard to expose securely, prefer polling first and move
to webhook delivery only after network access is stable.

## Related Documents

- [Product Overview](product-overview.md)
- [Issue Workflow](issue-workflow.md)
- [Configuration Guide](configuration.md)
- [n8n Node Reference](n8n-node-reference.md)
- [n8n Custom Node Development](../external/n8n/README.md)