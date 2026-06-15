# Python SDK Use And Validation

## Purpose

This guide gives contributors a project-level overview of the standalone Python
SDK that wraps the Ticket System Mock **REST API**.

Use it when you need to understand the SDK's role, install it locally, validate
it with the repository scripts, or extend its public surface alongside API
changes.

## Table of Contents

- [Role in the project](#role-in-the-project)
- [Repository location](#repository-location)
- [Current public surface](#current-public-surface)
- [Local install and quick use](#local-install-and-quick-use)
- [Bundled source distribution](#bundled-source-distribution)
- [Repository validation commands](#repository-validation-commands)
- [What make check and make test cover](#what-make-check-and-make-test-cover)
- [Live smoke validation](#live-smoke-validation)
- [Recommended contributor workflow](#recommended-contributor-workflow)
- [Related documents](#related-documents)

## Role in the Project

The Python SDK is a standalone **Integration System** for Python consumers of
the **REST API**.

Keep this boundary explicit:

- the **Web Application** remains the system of record
- the **REST API** remains the authoritative machine-facing contract
- the Python SDK wraps the REST API for sync and async Python callers
- the SDK must stay self-contained and must not depend on `src/webapp` runtime
  internals

When the REST API schema, payload rules, or endpoint behavior changes, treat the
SDK as part of the same shipped integration surface.

## Repository Location

The SDK lives under:

```text
src/ticketsystemmock/
```

Key files and directories:

- `pyproject.toml` defines the package metadata and runtime dependency on `httpx`
- `ticketsystemmock/client.py` defines the sync and async client entry points
- `ticketsystemmock/models/` contains the typed entity models returned by the SDK
- `ticketsystemmock/resources/` contains the resource-level wrappers around the API
- `ticketsystemmock/enums.py` exposes stable public constants for current API values
- `tests/tests_sdk.py` contains the SDK-focused unit tests
- `.coveragerc` configures the SDK coverage run used by the repository scripts

## Current Public Surface

The sync and async clients expose the same high-level resource layout:

- `system` for health checks
- `auth` for the authenticated user payload
- `profiles` for profile reads and profile updates
- `reference` for collections, categories, groups, and assignable users
- `board` and `dashboard` for the current read models
- `issues` for issue list, detail, create, update, move, and archive operations
- `comments` for comment add and update helpers
- `attachments` for attachment add, update, delete, and download helpers
- `admin.users` and `admin.groups` for superuser-only management endpoints
- `admin.workflow_state_auto_assignment_rules` for superuser-only workflow rule CRUD
- `admin.reset_instance(...)` for guarded superuser-only instance reset that preserves the authenticated superuser account

The package also exports typed enums for current API values, including:

- `IssuePriority`
- `WorkflowState`
- `CommentVisibility`
- `LanguagePreference`
- `AvatarType`

## Local Install and Quick Use

Create and sync the dedicated Python 3.14 virtual environment inside the SDK
directory:

```bash
cd src/ticketsystemmock
uv sync --python 3.14
```

Minimal sync example:

```python
from ticketsystemmock import IssuePriority, TicketSystemClient, WorkflowState

with TicketSystemClient("http://webapp:8000", "admin", "admin1234") as client:
    current_user = client.auth.me()
    issues = client.issues.list(priority=IssuePriority.HIGH, workflow_state=WorkflowState.NEW)
```

Minimal async example:

```python
from ticketsystemmock import AsyncTicketSystemClient


async def main():
    async with AsyncTicketSystemClient("http://webapp:8000", "admin", "admin1234") as client:
        health = await client.system.health()
        print(health.status)
```

    ## Bundled Source Distribution

    The web application can also ship the SDK as a downloadable source
    distribution on the authenticated `Integrations` page.

    This delivery path uses the same `build/integrations/` staging area as the
    bundled n8n package.

    Useful commands from the repository root:

    ```bash
    make update-devserver
    make ticketsystemmock-stage-dev-package
    make ticketsystemmock-validate-package
    ```

    Use `make update-devserver` when you want one command that restages all
    development-server artifacts after `make check` or `make test`, including
    the SDK download, the downloadable n8n package, the local n8n development
    mount, and the web application restart.

    Use `make ticketsystemmock-stage-dev-package` when you want the local
    development server at `http://webapp:8000/integrations/` to expose the SDK
    package. Use `make ticketsystemmock-validate-package` when you want to verify
    that the generated `sdist` contains the expected packaging files before
    shipping it.

    Operators who download the SDK from the Integrations page can install it into
    their own Python environment with:

    ```bash
    uv venv --python 3.14 .venv
    . .venv/bin/activate
    python -m pip install /path/to/ticketsystemmock-0.1.0.tar.gz
    ```

## Repository Validation Commands

The repository now includes a parallel validation flow for the SDK under
`scripts/ticketsystemmock/`.

Use these focused commands from the repository root:

```bash
make ticketsystemmock-compile
make ticketsystemmock-mypy-check
make ticketsystemmock-complexity-check
make ticketsystemmock-bandit-tests
make ticketsystemmock-unittest
make ticketsystemmock-test-coverage
```

These scripts create or reuse `src/ticketsystemmock/.venv` with Python 3.14 via
`uv`, install the SDK into that environment, and install the required
validation tools for type checking, complexity, security, and coverage checks.

Current SDK coverage gate:

- `ticketsystemmock-test-coverage` enforces a minimum total coverage of `98%`

This matches the repository-wide high coverage expectation for shipped
integration surfaces.

## What make check and make test Cover

The repository-level targets now include the SDK validation steps:

- `make check` runs SDK compile, mypy, complexity, bandit, and unittest checks
- `make test` runs SDK coverage before the webapp coverage pass

The SDK steps run before the broader webapp test phases so they are still
executed even if a later unrelated webapp test failure stops the overall target.

## Live Smoke Validation

When the development server is running, a small live smoke check can validate
that the SDK still works against the current API implementation.

From inside the dev container, prefer:

```bash
PYTHONPATH=src/ticketsystemmock /usr/local/python/current/bin/python - <<'PY'
from ticketsystemmock import TicketSystemClient

with TicketSystemClient("http://webapp:8000", "admin", "admin1234") as client:
    print(client.system.health().status)
    print(client.auth.me().username)
PY
```

The bootstrap superuser credentials come from the repository fixtures:

- username: `admin`
- password: `admin1234`

## Recommended Contributor Workflow

Use this sequence when changing the Python SDK:

1. update SDK code only inside `src/ticketsystemmock`
2. run the focused SDK targets, starting with `make ticketsystemmock-unittest`
3. run `make ticketsystemmock-mypy-check`, `make ticketsystemmock-complexity-check`, and `make ticketsystemmock-bandit-tests` when the change affects implementation structure
4. run `make ticketsystemmock-test-coverage` when the change affects shipped SDK behavior
5. run `make check` and, when appropriate, `make test` to keep the SDK validated as part of the full repository flow
6. run `make update-devserver` when the refreshed SDK package should be exposed
    through the local development server
7. run a live smoke check against `http://webapp:8000` when the change affects auth, transport, or request encoding behavior
8. update this document and the package `README.md` when the SDK surface or validation contract changes

## Related Documents

- [Application Architecture](../architecture/application-architecture.md)
- [Webapp Sitemap](webapp-sitemap.md)
- [n8n Node Use And Build](n8n-node-use-and-build.md)
- [Configuration Guide](../user/configuration.md)