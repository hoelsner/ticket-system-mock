# Ticket System Mock for Demos and Integrations

Ticket System Mock is a compact Django-based ticketing system
for demos, workflow walkthroughs, and integration scenarios.

<p align="center">
    <img src="src/webapp/static/img/default_app_hero_image.png" alt="Hero image" width="700">
</p>

It currently provides:

- an authenticated user frontend with a Kanban board, personal dashboard, and
	issue workflows
- configurable branding for the application display name, navbar logo, and
	login background illustration
- a Django Admin surface for data and branding management
- a Django Ninja REST API that mirrors the main issue and board workflows for
	automation and integrations
- a standalone Python SDK under `src/ticketsystemmock` that wraps the REST API
	for sync and async Python consumers and can be downloaded from the
	authenticated Integrations page as a pip-installable source distribution
- a bundled private n8n node package that can be downloaded from the web
	application Integrations page and installed into an n8n instance

## Production Deployment with Docker Compose

The repository ships a production-style Docker Compose stack in
`deploy/docker-compose/`. The stack uses one reusable web application image for
the `management` and `webapp` services plus separate PostgreSQL, Redis, and
NGINX containers.

### Option 1: Use an Image from a Central Container Registry

Use this option when you only need to run the stack and do not want to keep the
full repository on the target host. The published Docker Hub image
`hoelsner/ticket-system-mock:latest` is the recommended production default.

1. Prepare a deployment directory on the target host.
2. Copy the generated deployment bundle there, or copy these files manually:
	- `deploy/docker-compose/docker-compose-template.yaml` as
	  `docker-compose.yaml`
	- `deploy/docker-compose/docker-compose.template.override.yaml` as
	  `docker-compose.override.yaml`
3. Create a `.env` file next to `docker-compose.yaml`.
4. Set at least these values in `.env`:

```env
DJANGO_SECRET_KEY=replace-this-with-a-secret-value
SERVICE_BASE_URL=https://localhost:8443
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_PASSWORD=replace-this-with-a-secret-value
CACHE_PASSWORD=replace-this-with-a-secret-value
NGINX_SERVER_NAME=localhost
NGINX_HTTP_PORT=8080
NGINX_HTTPS_PORT=8443
```

The compose template already defaults `WEBAPP_IMAGE` to
`hoelsner/ticket-system-mock:latest`, so the `.env` file does not need to set
it. These defaults are aimed at a local production-style test setup. For an actual
hosted deployment, replace `SERVICE_BASE_URL`, `DJANGO_ALLOWED_HOSTS`,
`NGINX_SERVER_NAME`, and the published ports as needed for the target hostname.

5. Pull the referenced images:

```bash
docker compose -f docker-compose.yaml pull
```

6. Start the stack:

```bash
docker compose -f docker-compose.yaml up -d
```

7. Verify that the one-off management container completed successfully before
	relying on the web application:

```bash
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs management
```

The application is then available through the NGINX container on the configured
HTTP and HTTPS ports.

### Option 2: Build and Deploy from a Full Repository Checkout

Use this option when the full repository is available on the deployment host and
you want to build the web application image locally instead of using the
published Docker Hub image.

1. Build a versioned image and generate a deployment bundle:

```bash
IMAGE_REPOSITORY=localhost.local/ticket-system-mock-webapp \
deploy/build_scripts/build_environment.bash 20260605-1
```

This command:

- builds the image `localhost.local/ticket-system-mock-webapp:20260605-1`
- stores the build metadata in the image
- creates a ZIP deployment bundle under `build/deploy/`

2. Copy the generated compose files from the bundle into the deployment working
	directory, or copy the templates from `deploy/docker-compose/` into the
	repository root as `docker-compose.yaml` and `docker-compose.override.yaml`.
3. Create `.env` next to `docker-compose.yaml` with the required secrets and
	host-specific runtime settings.
4. Start the production stack from the repository root:

```bash
docker compose -f docker-compose.yaml up -d
```

5. Review the startup state:

```bash
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs management
docker compose -f docker-compose.yaml logs webapp
```

If you only need the deployment assets after the image has already been built,
set `SKIP_DOCKER_BUILD=1` before running the build script. This reuses the
existing image tag and only regenerates the ZIP bundle.

Key documentation entry points:

- [Product Overview](docs/user/product-overview.md)
- [Configuration Guide](docs/user/configuration.md)
- [Issue Workflow](docs/user/issue-workflow.md)
- [n8n Integration Guide](docs/user/n8n-integration.md)
- [n8n Node Reference](docs/user/n8n-node-reference.md)
- [Application Architecture](docs/architecture/application-architecture.md)
- [Webapp Sitemap](docs/development/webapp-sitemap.md)
- [Python SDK Use And Validation](docs/development/python-sdk-use-and-validation.md)
- [n8n Node Use And Build](docs/development/n8n-node-use-and-build.md)

## n8n Integration

The repository includes a private `n8n` custom node package under
`src/n8n_node`. The packaged file is bundled into the web application build
and exposed to signed-in users through the Integrations page. Operators
download that file and place the package under
`~/.n8n/custom/node_modules/n8n-nodes-ticket-system-mock/` on the target `n8n`
instance.

Use the user-facing guide when you want to connect `n8n` to a deployed Ticket
System Mock instance:

- [n8n Integration Guide](docs/user/n8n-integration.md)
- [n8n Node Reference](docs/user/n8n-node-reference.md)

Use the development documentation when you need to build, package, or smoke-test
the custom node locally:

- [n8n Node Use And Build](docs/development/n8n-node-use-and-build.md)
- [n8n Local Smoke Test](docs/development/n8n-local-smoke-test.md)

## Python SDK

The repository also includes a standalone Python SDK under:

```text
src/ticketsystemmock/
```

This package mirrors the current REST API contract and exposes sync and async
clients plus entity models for Python-based **Integration System** consumers.
The authenticated Integrations page can also serve the packaged SDK as a
downloadable source distribution for separate Python environments.

Use the contributor guide when you need to install, validate, or extend the SDK:

- [Python SDK Use And Validation](docs/development/python-sdk-use-and-validation.md)

