# Webapp Sitemap

## Purpose

This sitemap gives contributors a current view of the Django web application
route structure. It summarizes the user frontend, authentication endpoints,
admin surface, and REST API so route ownership stays easy to understand during
development.

## Table of Contents

- [Route Ownership](#route-ownership)
- [Top-Level Sitemap](#top-level-sitemap)
- [Resolved Route Tree](#resolved-route-tree)
- [Notes for Contributors](#notes-for-contributors)

## Route Ownership

- `/` is owned by `djangoapp.user_interface` and serves the authenticated user
  frontend. Within that frontend, the main user touchpoints should be the
  `Personal Dashboard`, the `Instance Kanban Board`, and the `Issue Detail View`.
- `/accounts/` is provided by Django's built-in authentication URL set and
  supports session-based login flows.
- `/admin/` is provided by Django Admin and serves the authenticated admin
  frontend.
- `/admin/` also hosts the `App Branding` management surface used to override
  the display name, navbar logo, login background image, login screen message,
  and login message level.
- `/api/` is owned by `djangoapp.rest_api` and exposes the machine-facing REST
  API protected by HTTP Basic Authentication.

## Top-Level Sitemap

```mermaid
flowchart TD
  A[Web Application]
  A --> B[User Frontend at /]
  B --> C[Personal Dashboard]
  B --> D[Instance Kanban Board]
  B --> E[Issue Detail View]
  B --> I[Create New Issue]
  B --> J[Update Existing Issue]
  B --> K[Archive Issue]
  E --> L[Issue Card Summary Component]
  L --> M[Add Comment]
  A --> F[Session Auth at /accounts/]
  A --> G[Admin Frontend at /admin/]
  A --> H[REST API at /api/]
  H --> N[OpenAPI Schema]
  H --> O[API Docs]
  H --> P[Health Check]
  H --> Q[Authenticated User Lookup]
```

## User Frontend Pages and Components

- `Personal Dashboard`: shows the user's direct issue assignments and issue
  comments where the user was mentioned.
- `Instance Kanban Board`: shows the overall operational board grouped by
  workflow state. The same page also supports `?fullscreen=1` to suppress the
  authenticated shell chrome for presentation use.
- `Issue Detail View`: shows the full issue title, markdown description,
  comments, and workflow context.
- `Create New Issue`: starts a new issue in the user frontend.
- `Update Existing Issue`: edits an existing issue when reached from the
  `Personal Dashboard` or the `Instance Kanban Board`.
- `Archive Issue`: archives an issue using soft-delete behavior rather than a
  hard delete.
- `Issue Card Summary Component`: provides the reusable summary card used for an
  issue in list and board contexts.
- `Add Comment`: must be available anywhere the `Issue Card Summary Component`
  is visible.

## REST API Operations

- `OpenAPI Schema`: available at `/api/openapi.json` for machine-readable API
  discovery.
- `API Docs`: available at `/api/docs` as the interactive Django Ninja
  documentation UI.
- `Health Check`: available at `/api/health` and returns the basic API health
  status.
- `Authenticated User Lookup`: available at `/api/auth/me` and returns the
  authenticated user's username and privilege flags.
- `Reference Data`: available at `/api/groups`, `/api/users`,
  `/api/collections`, and `/api/categories` for integration-friendly metadata.
  These list endpoints return their arrays under the root `data` key. The
  `/api/users` list returns active users only so integrations resolve
  assignable accounts.
- `Administrative User and Group Management`: available at `POST /api/users`,
  `GET|PUT|DELETE /api/users/{user_id}`, `POST /api/groups`, and
  `GET|PUT|DELETE /api/groups/{group_id}`. These endpoints require a superuser.
  User deletion deactivates the account, while group deletion is rejected when
  an `Issue` still references that `Group`.
- `Board Projection`: available at `/api/board` and returns the filtered board
  context used by the user frontend.
- `Dashboard Projection`: available at `/api/dashboard` and returns the current
  user's assigned issues and mentions.
- `Issue Listing and Detail`: available at `/api/issues` and
  `/api/issues/{issue_id}`. The `/api/issues` list endpoint returns matching
  issues under the root `data` key.
- `Issue Mutations`: available at `/api/issues`, `/api/issues/{issue_id}`,
  `/api/issues/{issue_id}/archive`, `/api/issues/{issue_id}/comments`, and
  `/api/issues/{issue_id}/move`.

## Resolved Route Tree

The following tree reflects the currently resolved Django URL patterns,
including routes that come from Django's built-in auth and admin modules and
from Django Ninja.

```text
/
accounts/
  login/
  logout/
  password_change/
  password_change/done/
  password_reset/
  password_reset/done/
  reset/<uidb64>/<token>/
  reset/done/
admin/
  login/
  logout/
  password_change/
  password_change/done/
  autocomplete/
  jsi18n/
  r/<path:content_type_id>/<path:object_id>/
  auth/group/
  auth/group/add/
  auth/group/<path:object_id>/history/
  auth/group/<path:object_id>/delete/
  auth/group/<path:object_id>/change/
  auth/group/<path:object_id>/
  auth/user/
  auth/user/add/
  auth/user/<id>/password/
  auth/user/<path:object_id>/history/
  auth/user/<path:object_id>/delete/
  auth/user/<path:object_id>/change/
  auth/user/<path:object_id>/
api/
  openapi.json
  docs
  health
  auth/me
  groups
  groups/{group_id}
  users
  users/{user_id}
  users/{username}/profile
  collections
  categories
  board
  dashboard
  issues
  issues/{issue_id}
  issues/{issue_id}/archive
  issues/{issue_id}/comments
  issues/{issue_id}/move
```

## Notes for Contributors

- Keep the user frontend route declarations in `djangoapp.user_interface.urls`.
- Keep the REST API route declarations in `djangoapp.rest_api.urls` and
  `djangoapp.rest_api.api`.
- Keep the REST API operation list in this document aligned with the concrete
  endpoints registered on the Django Ninja `api` object.
- Keep `/api/docs` and `/api/openapi.json` aligned with the concrete REST API
  contract by updating endpoint summaries, descriptions, tags, request payload
  metadata, and schema field descriptions in `djangoapp.rest_api.api` whenever
  an endpoint or payload changes.
- Keep the admin-facing branding notes aligned with the registered
  `djangoapp.branding` admin model.
- Treat the `Personal Dashboard`, the `Instance Kanban Board`, and the `Issue
  Detail View` as the primary user-facing entry points inside the authenticated
  user frontend.
- Allow users to create issues, update issues, archive issues, and add comments
  from the user frontend where those flows are visible.
- Keep issue-card-based interactions consistent so commenting is available
  anywhere the reusable issue card summary is shown.
- Treat `/accounts/` and `/admin/` as framework-provided surfaces that still
  belong to the web application sitemap even though the individual route
  handlers are supplied by Django.
- Update this document when new route groups, user pages, admin extensions, or
  API endpoints are added.