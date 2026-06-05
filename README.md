# IT Operation Ticketing Demo Service

IT Operation Ticketing Demo Service is a compact Django-based ticketing system
for demos, workflow walkthroughs, and integration scenarios.

It currently provides:

- an authenticated user frontend with a Kanban board, personal dashboard, and
	issue workflows
- configurable branding for the application display name, navbar logo, and
	login background illustration
- a Django Admin surface for data and branding management
- a Django Ninja REST API that mirrors the main issue and board workflows for
	automation and integrations

Key documentation entry points:

- [Product Overview](docs/user/product-overview.md)
- [Configuration Guide](docs/user/configuration.md)
- [Issue Workflow](docs/user/issue-workflow.md)
- [Application Architecture](docs/architecture/application-architecture.md)
- [Webapp Sitemap](docs/development/webapp-sitemap.md)

## Production Deployment with Docker Compose

The repository ships a production-style Docker Compose stack in
`deploy/docker-compose/`. The stack uses one reusable web application image for
the `management` and `webapp` services plus separate PostgreSQL, Redis, and
NGINX containers.

### Option 1: Use an Image from a Central Container Registry

Use this option when you only need to run the stack and do not want to keep the
full repository on the target host.

1. Prepare a deployment directory on the target host.
2. Copy the generated deployment bundle there, or copy these files manually:
	- `deploy/docker-compose/docker-compose-template.yaml` as
	  `docker-compose.yaml`
	- `deploy/docker-compose/docker-compose.template.override.yaml` as
	  `docker-compose.override.yaml`
3. Create a `.env` file next to `docker-compose.yaml`.
4. Set at least these values in `.env`:

```env
WEBAPP_IMAGE=registry.example.com/your-org/itoperation-ticketing-demo-service:20260605-1
DJANGO_SECRET_KEY=replace-this-with-a-secret-value
DJANGO_ALLOWED_HOSTS=ticketing.example.com
POSTGRES_PASSWORD=replace-this-with-a-secret-value
CACHE_PASSWORD=replace-this-with-a-secret-value
NGINX_SERVER_NAME=ticketing.example.com
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

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
you want to build the web application image locally.

1. Build a versioned image and generate a deployment bundle:

```bash
IMAGE_REPOSITORY=itoperation-ticketing-demo-service \
deploy/build_scripts/build_environment.bash 20260605-1
```

This command:

- builds the image `itoperation-ticketing-demo-service:20260605-1`
- stores the build metadata in the image
- creates a ZIP deployment bundle under `build/deploy/`

2. Copy the generated compose files from the bundle into the deployment working
	directory, or copy the templates from `deploy/docker-compose/` into the
	repository root as `docker-compose.yaml` and `docker-compose.override.yaml`.
3. Create `.env` next to `docker-compose.yaml` and set `WEBAPP_IMAGE` to the
	image tag produced by the build script together with the required secrets.
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

