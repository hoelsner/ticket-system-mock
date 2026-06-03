# Django Cotton Basic Usage

## Purpose

This guide summarizes the basic project usage of Django Cotton for the user
frontend.

## Role in This Project

Django Cotton is the component layer for the user frontend. It helps structure
reusable UI pieces on top of Django views and templates.

The user frontend that uses Cotton should be protected with Django
session-based authentication.

## Installation and Setup

Add Cotton to `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    "django_cotton",
]
```

If the project uses custom template loader configuration, Cotton also supports a
manual setup mode with its own loader and builtins.

## Component Location

Store components in a `templates/cotton/` directory at app level or project
level.

Examples:

- `templates/cotton/card.html`
- `templates/cotton/ticket/status_badge.html`

## Basic Component

Component template:

```html
<article>
    <h3>{{ title }}</h3>
    <div>{{ slot }}</div>
</article>
```

Template usage:

```html
<c-card title="Open Tickets">
    Review items waiting for triage.
</c-card>
```

## Passing Data

Use attributes for simple values and `:`-prefixed attributes for variables or
expressions.

```html
<c-ticket.row :ticket="ticket" />
```

## Named Slots

Use named slots when a component needs more than one content area.

```html
<c-panel>
    <c-slot name="header">
        Ticket Summary
    </c-slot>
    Main panel content
</c-panel>
```

## HTMX-Friendly Components

Cotton components work well with HTMX because HTMX attributes can be passed
through component attributes.

```html
<c-button hx-get="/tickets/1" hx-target="#ticket-detail">
    Load Ticket
</c-button>
```

## Project Guidance

- Use Cotton for the user frontend, not for Django Admin or the REST API.
- Keep components small and aligned with product concepts such as Ticket cards,
  status badges, assignment widgets, and board columns.
- Keep user frontend views behind the login page and use Cotton only inside the
    authenticated UI surface.
- Place reusable view fragments in `templates/cotton/` and render page shells
  with normal Django templates.