# Product Overview

## Purpose

Ticket System Mock is a lightweight ticketing system for demos,
workflow simulations, and integration scenarios. It provides a realistic IT
operations workflow without the overhead of a full ITSM platform.

## Who Uses It

- Demo presenters who need a predictable ticketing workflow for walkthroughs
- Support users who triage, assign, and process tickets
- Group leads who monitor workload and bottlenecks
- External systems that create or update tickets through the API

## Core Workflow

The application uses a fixed ticket lifecycle so demos and integrations behave
consistently.

```text
New
-> Triage
-> Assigned
-> In Progress
-> Waiting
-> Resolved
-> Closed
```

Exceptional handling uses `Rejected` when a ticket does not follow the
standard path. `Escalated` remains a separate flag, not a workflow state.

## Main Capabilities

- Create and update tickets
- View ticket details and operational metadata
- Assign work to groups and individual users
- Move tickets through the predefined workflow
- Track ownership, priority, category, status, and timestamps
- Monitor work on a Kanban board
- Toggle the Kanban board into a fullscreen presentation mode
- Configure per-user language, avatar type, avatar image, and system-user avatar behavior
	through a dedicated profile settings view
- Open public user profiles from assignee names, comment authors, and user
	mentions
- Customize the displayed product name, navbar logo, login background, and
	login screen message

## Interface Structure

The application uses two main interface structures.

### Authentication view

The login or sign-up experience should use a split layout with a clear visual
hierarchy.

- The left panel contains the functional authentication content such as the
	title, short description, form fields, legal acknowledgement, primary action,
	and secondary sign-in or sign-up link.
- The right panel contains a large product illustration that communicates the
	operational or industrial context of the application.
- The left side is interaction-focused, while the right side is contextual and
	brand-oriented.

### Authenticated application shell

Once authenticated, the application should use a top-down layout with global
navigation and secondary side navigation.

1. A persistent top navigation bar provides the primary navigation areas of the
	 application.
2. A burger menu in the top-left corner opens a collapsible detailed navigation
	 panel for deeper module navigation and contextual actions.
3. The detailed navigation panel contains Administration, Healthcheck, API
	 Docs, sign-out, and the current user context.
4. A utility area in the top-right corner provides the fullscreen shortcut,
	 the current user context, profile settings access, and sign-out.
5. The main content area is reserved for dashboards, issues, forms, tables,
	 reports, and other workflow-specific views.

Clicking the signed-in username opens the authenticated user's profile settings.
Other user names in issue and comment views open a public profile view that is
read-only for viewers.

For presentation-heavy walkthroughs, the `Instance Kanban Board` can also be
opened in a fullscreen mode that hides the top navigation, page title, and
search and filter controls while keeping the board content itself available.

## Kanban Board

The default post-login landing page is the personal dashboard. The Kanban board
remains the main operational overview for workflow state. Each column
represents a workflow phase, and each card represents a ticket. The board is
intended to reflect the current operational state and support live updates
without a full page reload.

The standard board view also includes search and filter controls for assignee,
priority, collection, and category. When needed for demos or wallboard-style
display, the board can be switched into fullscreen mode from the board header.
The fullscreen toggle keeps the active board filters when entering or leaving
that mode.

## Integration Use

The web application exposes a REST API for automation and external systems.
Integrations can create, enrich, query, or transition tickets while the web
application remains the source of truth for workflow state and business rules.

The API includes metadata endpoints, board and dashboard projections, issue
listing and detail responses, issue mutation operations for create, update,
archive, comment, and board movement workflows, and user profile endpoints for
reading and updating language preferences, avatar type preferences, avatar
images, and the system-user flag. Superusers can also manage Django `User` and
`Group` records through dedicated REST API endpoints, while the general user
list remains scoped to active accounts.

## Product Boundaries

Included:

- Mock ticketing workflows for demos and simulations
- Kanban-based ticket visualization
- REST API for external integrations
- Group and individual dispatching
- Backend administration through Django Admin
- Configurable product display name
- Configurable navbar logo and login background artwork
- Configurable login screen message and message level

Not included in the initial scope:

- Full ITSM suite functionality
- Arbitrary workflow customization
- SLA management
- Multi-tenancy
- Real identity-provider integration unless added explicitly

## Positioning

This project is not intended to replace tools such as Jira or ServiceNow. It is
designed to be compact, controllable, and easy to integrate for demo and
prototype scenarios.