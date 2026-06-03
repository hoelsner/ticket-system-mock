# Application Technology Reference

## Purpose

This document summarizes the primary technologies used by the application and
their role in the system. It is intended as a reference for contributors who
need to understand the external frameworks and platform choices used in the
project.

## Backend Technologies

### Python

The application runtime is based on Python.

### Django

Django provides the core web application framework, request handling, template
rendering, configuration, and administrative tooling.

### Django Admin

Django Admin supports backend administration and internal data management.

### Django Ninja

Django Ninja is used to expose the REST API consumed by external systems and the
n8n custom node.

### Relational database

A relational database persists tickets, teams, assignments, workflow state, and
other application records.

## Frontend Technologies

### Server-side rendering

The application renders HTML on the server to keep the UI simple and predictable
for demo workflows.

The project separates this into two human-facing surfaces:

- a user frontend built with Django views, Django templates, Django Cotton, and
	Pico CSS
- an admin frontend built with Django Admin

### HTMX

HTMX supports partial page updates and interactive UI behavior without requiring
a full client-side SPA architecture.

### Server-Sent Events

Server-Sent Events are intended for live Kanban board updates so workflow
changes appear without a full page refresh.

### Django Cotton

Django Cotton is used for reusable UI component patterns in the user frontend.

### Pico CSS

Pico CSS provides the baseline visual styling for the user frontend.

## Integration Technologies

### REST API

The Django application exposes a REST API that external tools use to create,
query, update, and transition tickets.

The REST API is implemented with Django Ninja and is separate from both the user
frontend and the admin frontend.

### n8n custom node

The custom n8n node is an API consumer for automation and integration flows. It
must stay separate from the web application's business logic.

## System Role Boundaries

- The web application is the system of record.
- The user frontend is built with Django views, Cotton, and Pico CSS.
- The admin frontend is built with Django Admin.
- The REST API is built with Django Ninja.
- The web application owns business rules, workflow state, and API contracts.
- External integrations consume the API rather than sharing internal logic.

## Related Documentation

- For product behavior, see the user documentation.
- For container topology and runtime roles, see the architecture documentation.