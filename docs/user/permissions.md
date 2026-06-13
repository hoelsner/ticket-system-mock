# Permissions Guide

## Purpose

This guide explains the implemented access model of Ticket System Mock. It
describes how `User`, `Group`, and permission-related concepts work in the
application and clarifies which authenticated actors can perform which actions.

## Overview

Ticket System Mock uses Django authentication as the base access mechanism.

The implemented permission model is intentionally simple:

- A signed-in `User` can use the authenticated web interface.
- A valid active API user can use the authenticated REST API.
- Superuser-only REST API endpoints manage Django `User` and `Group` records.
- Django `Group` membership is used for dispatch and assignment validation.
- Django admin access remains limited to staff users through the standard Django
  admin site.
- The application does not implement a separate fine-grained role-based
  permission layer for issue actions such as create, update, archive, comment,
  or attachment management.

## Authentication Model

### Web application

Most user-facing HTML pages require a signed-in session.

This includes:

- the `Instance Kanban Board`
- the `Personal Dashboard`
- issue create, update, archive, comment, and attachment actions
- public user profile pages inside the authenticated application
- the profile settings page
- the authenticated healthcheck status page

Unauthenticated users are redirected to the login page.

### REST API

The REST API requires HTTP Basic authentication with a valid active Django
`User`.

This applies to the documented `/api/` endpoints, including:

- `/api/auth/me`
- issue endpoints
- reference data endpoints
- profile endpoints
- `/api/health`

Most REST API endpoints remain available to any active authenticated `User`.

The following management endpoints additionally require a Django `superuser`:

- `POST /api/users`
- `GET /api/users/{user_id}`
- `PUT /api/users/{user_id}`
- `DELETE /api/users/{user_id}`
- `POST /api/groups`
- `GET /api/groups/{group_id}`
- `PUT /api/groups/{group_id}`
- `DELETE /api/groups/{group_id}`

### Public healthcheck endpoint

The non-API healthcheck JSON endpoint is publicly reachable without login.

This is different from the authenticated healthcheck status page in the web
application.

## Users

A `User` is the main authenticated actor in the application.

Implemented capabilities for any authenticated `User` include:

- view the `Instance Kanban Board`
- view the `Personal Dashboard`
- create an `Issue`
- update an `Issue`
- archive an `Issue`
- move an `Issue` on the board
- add `Issue Comment` entries
- upload and delete issue attachments
- view other users' public profiles
- view and update their own profile settings

The application currently does not restrict issue mutations to the creator,
current assignee, or members of a specific `Group`.

## Groups

A Django `Group` represents a dispatch unit for issues.

Implemented group behavior:

- an `Issue` can be associated with zero or one `Group`
- a `User` can belong to multiple groups through standard Django group
  membership
- the issue forms can filter assignable users by the selected `Group`
- when a `User` is assigned to an `Issue`, that user must belong to the chosen
  `Group`
- a configured workflow-state auto-assignment rule can set the `Group` and
  optionally the `User` during a workflow transition
- if a workflow-state auto-assignment rule sets a `Group` without a `User`, the
  issue remains assigned only to that `Group` until a `User` from that `Group`
  takes ownership

`Group` membership is therefore used for assignment consistency, not as a
general access-control boundary.

Being outside a `Group` does not block an authenticated user from opening or
editing an issue.

## Administrative User and Group Management

The REST API now includes a small administrative surface for superusers.

Implemented management behavior:

- superusers can create, inspect, and update Django `User` records through the
  REST API
- superusers can set Django `Group` memberships through the same user and group
  management endpoints
- deleting a user through the REST API deactivates that user by setting
  `is_active` to `False` instead of removing the database row
- deleting a group through the REST API is rejected while an `Issue` still
  references that group
- the general `/api/users` list endpoint returns active users only so
  integrations resolve assignable users instead of deactivated accounts

## Django Permissions and Roles

The application exposes Django's `is_staff` and `is_superuser` flags through
the API. The user-facing issue workflow still does not use additional explicit
Django permission checks such as per-model `add`, `change`, `delete`, or custom
permission gates.

In practical terms:

- staff and superuser flags matter for Django admin access
- superuser also gates the REST API endpoints that manage Django `User` and
  `Group` records
- standard authenticated users can still perform the main issue workflow in the
  web UI and REST API
- no separate application role such as read-only user, dispatcher, or group
  lead is enforced in code

## Profile Access Rules

Profile access follows two different rules.

### Public profile visibility

Any authenticated `User` can open another user's public profile page and can
retrieve another user's public profile through the REST API.

Public profile information includes:

- display name
- username
- language preference display value
- system-user flag
- resolved avatar presentation
- group memberships
- assigned active issue count

### Profile editing

Only the signed-in owner of a profile can edit that profile.

This applies to:

- the profile settings page in the web application
- the `/api/profile/me` update endpoint

When another user's profile is retrieved through the API, the payload marks the
profile as not editable for that caller.

## Action Matrix

| Action | Anonymous visitor | Authenticated `User` | Staff user | Superuser |
| --- | --- | --- | --- | --- |
| Open login page | Yes | Yes | Yes | Yes |
| Open authenticated web pages | No | Yes | Yes | Yes |
| Use REST API | No | Yes | Yes | Yes |
| Open public healthcheck JSON endpoint | Yes | Yes | Yes | Yes |
| Open authenticated healthcheck status page | No | Yes | Yes | Yes |
| View `Instance Kanban Board` and `Personal Dashboard` | No | Yes | Yes | Yes |
| Create, update, archive, or move an `Issue` | No | Yes | Yes | Yes |
| Add or remove issue attachments | No | Yes | Yes | Yes |
| Add `Issue Comment` entries | No | Yes | Yes | Yes |
| View another user's public profile | No | Yes | Yes | Yes |
| Edit own profile settings | No | Yes | Yes | Yes |
| Edit another user's profile settings | No | No | No through the user-facing profile flows | No through the user-facing profile flows |
| Create, update, or deactivate a user through the REST API | No | No | No | Yes |
| Create, update, or delete a group through the REST API | No | No | No | Yes |
| Access Django admin | No | No unless marked as staff | Yes | Yes |

## Important Current Limits

The implemented permission system currently has these limits:

- issue access is broad for authenticated users and is not limited by creator,
  assignee, or `Group`
- `Group` membership validates assignment choices but does not enforce issue
  visibility
- the application does not define a separate business permission model beyond
  authentication, Django admin access, superuser-only user and group
  management, and owner-only profile editing
- API authentication uses username and password over HTTP Basic Auth rather than
  token-based access

## Related Documentation

- See [product-overview.md](product-overview.md) for the product structure and
  main user-facing capabilities.
- See [issue-workflow.md](issue-workflow.md) for the lifecycle and main
  user-facing actions on an `Issue`.