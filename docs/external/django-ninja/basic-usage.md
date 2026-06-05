# Django Ninja Basic Usage

## Purpose

This guide summarizes the basic project usage of Django Ninja as the REST API
layer.

## Role in This Project

Django Ninja provides the machine-facing API surface for integrations,
automation, and the n8n custom node.

## Basic Setup

Create a `NinjaAPI` instance and expose it through the Django URL
configuration.

```python
from ninja import NinjaAPI
from ninja.security import HttpBasicAuth


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password): ...


api = NinjaAPI(auth=BasicAuth())
```

Mount the API under a dedicated URL prefix.

```python
from django.contrib import admin
from django.urls import path

from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
```

## Basic Endpoint

Define endpoints directly on the API instance.

```python
from ninja import NinjaAPI

api = NinjaAPI()


@api.get("/health")
def health(request):
    return {"status": "ok"}
```

## Schemas

Use typed schemas for request and response shapes.

```python
from ninja import Schema


class TicketSchema(Schema):
    ticket_number: str
    title: str
    workflow_state: str
```

```python
from ninja import NinjaAPI

api = NinjaAPI()


@api.get("/tickets/{ticket_id}", response=TicketSchema)
def get_ticket(request, ticket_id: int):
    return {
        "ticket_number": "INC-1001",
        "title": "VPN access issue",
        "workflow_state": "TRIAGE",
    }
```

## Testing API Endpoints

Django Ninja supports two useful testing styles:

- Django's standard test client for end-to-end API behavior through URL routing,
    authentication, and middleware
- Ninja's `TestClient` for focused API tests that call the API layer directly

### Use Django's test client for project endpoint tests

In this project, prefer Django's standard test client when testing the REST API
endpoints exposed under `/api/`.

This is the better default when you want to verify:

- URL routing under `/api/`
- HTTP Basic Authentication behavior
- response status codes and payloads as seen by external clients
- integration with Django request handling

Example:

```python
import base64

from django.test import TestCase


class ApiAuthenticationTests(TestCase):
    def basic_auth_header(self, username, password):
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    def test_health_endpoint_requires_basic_auth(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 401)

    def test_health_endpoint_returns_ok_for_valid_credentials(self):
        response = self.client.get(
            "/api/health",
            headers=self.basic_auth_header("demo", "demo-password-123"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
```

### Use Ninja `TestClient` for focused API-layer tests

The official Django Ninja testing guide also recommends `ninja.testing.TestClient`
for faster tests that bypass Django middleware and URL resolution.

Use this style when you want to test:

- endpoint logic in isolation
- simple request and response behavior on a router or API object
- request attributes injected directly for a focused unit-style test

Example:

```python
from django.test import TestCase
from ninja.testing import TestClient

from djangoapp.api import api


class ApiLogicTests(TestCase):
    def test_health_endpoint_returns_ok(self):
        client = TestClient(api)

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
```

The official guide also shows that `TestClient` can inject request data directly.
For example, you can pass a `user=` argument to simulate an authenticated user
or add request attributes with keyword arguments when the endpoint depends on
request-scoped values.

### Project guidance

- Prefer Django's standard test client for public API endpoint tests in this
    repository.
- Use Ninja `TestClient` only for focused API-layer tests where bypassing the
    full Django request path is intentional.
- Keep authentication tests explicit by checking both unauthorized and
    authorized cases.
- Assert both status codes and response payloads so the API contract stays
    stable.

## Swagger and OpenAPI Maintenance

In this repository, the Django Ninja declarations in `djangoapp.rest_api.api`
are the source of truth for the interactive API documentation at `/api/docs`
and the generated schema at `/api/openapi.json`.

When changing or adding REST API endpoints:

- add an explicit `summary`, `description`, and `tags` value on the endpoint
    decorator instead of relying on the generated defaults
- describe query parameters with `Query(..., description=...)` when filters or
    selectors appear in the URL
- describe every response schema attribute with `Field(description=...)` so the
    schema explains nested objects and scalar fields in Swagger UI
- document request payloads for JSON or multipart mutations so integrations can
    see the accepted attributes directly in Swagger UI
- keep the terminology aligned with the repository's ubiquitous language,
    especially `Issue`, `Workflow State`, `Collection`, `Group`, and `User`

When changing the API contract:

- request `/api/openapi.json` in a Django test and assert representative
    summaries, request-body attributes, and schema field descriptions
- review `/api/docs` manually for the touched endpoints to confirm the rendered
    documentation stays readable and complete

## Project Guidance

- Keep the REST API under `/api/`.
- Protect the REST API with HTTP Basic Authentication.
- Use Django Ninja for system-to-system contracts, not for the user frontend.
- Reuse the same domain rules as the user frontend and admin frontend.
- Expose domain operations and data models through the API, not only through
    HTML views or the admin frontend.
- Organize API logic in dedicated `api.py` or router modules instead of mixing
  it into HTML views.