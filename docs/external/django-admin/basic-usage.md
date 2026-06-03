# Django Admin Basic Usage

## Purpose

This guide summarizes the basic project usage of Django Admin as the internal
administration frontend.

## Role in This Project

Django Admin is the admin-facing surface of the application. It is used for
record inspection, maintenance tasks, and reference data management. It is not
the primary product workflow UI.

## Basic Setup

Django Admin is included with Django. The project needs:

- `django.contrib.admin` in `INSTALLED_APPS`
- an admin route in the main URL configuration
- registered models in each app's `admin.py`
- a superuser for interactive access

## URL Configuration

Expose the admin site through a dedicated route.

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
```

## Registering Models

For basic CRUD access, register the model with the admin site.

```python
from django.contrib import admin

from .models import Ticket

admin.site.register(Ticket)
```

For customized list views, search, or filters, define a `ModelAdmin`.

```python
from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "title", "workflow_state", "priority")
    list_filter = ("workflow_state", "priority")
    search_fields = ("ticket_number", "title")
```

## Access

Create an admin user with:

```bash
python manage.py createsuperuser
```

Then sign in through `/admin/`.

Django Admin uses Django's session-based authentication flow.

## Project Guidance

- Use Django Admin for administration, not as a substitute for the user
  frontend.
- Register core entities such as Tickets, Teams, Agents, Assignments, and
  configuration records.
- Keep admin access behind authenticated Django sessions.
- Keep admin customization pragmatic. Add filters, search, and list displays
  before building more advanced overrides.