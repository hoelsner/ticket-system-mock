# Local Build And Production Test Verification

## Purpose

This guide documents the full local verification flow for the production image,
deployment bundle, and production-style Docker Compose stack.

Use this flow when you want to verify that:

- the web application image builds locally
- the deployment bundle is generated correctly
- the production-style stack starts from the generated bundle
- the HTTPS entrypoint and admin login work end to end

## Prerequisites

Run all commands from the repository root.

Required tools:

- `docker`
- `curl`
- `openssl`
- `unzip`

Recommended repository checks before the production-style test:

```bash
make check
make test
```

## 1. Build The Local Production Image And Bundle

Use the fixed build version `test-bundle` so the generated ZIP name matches the
default path used by `scripts/setup_production_test_instance.bash`.

```bash
IMAGE_REPOSITORY=localhost.local/ticket-system-mock-webapp \
deploy/build_scripts/build_environment.bash test-bundle
```

Expected outputs:

- local image `localhost.local/ticket-system-mock-webapp:test-bundle`
- bundle directory `build/deploy/ticket-system-mock-test-bundle`
- bundle archive `build/deploy/ticket-system-mock-test-bundle.zip`

## 2. Verify The Build Outputs

Confirm that the local image and bundle exist:

```bash
docker image inspect localhost.local/ticket-system-mock-webapp:test-bundle --format '{{.Id}}'
ls -1 build/deploy/ticket-system-mock-test-bundle build/deploy/ticket-system-mock-test-bundle.zip
cat build/deploy/ticket-system-mock-test-bundle/build-metadata.env
```

The `build-metadata.env` file should point `WEBAPP_IMAGE` at the locally built
image tag.

When `WEBAPP_IMAGE` points at a local-only tag such as
`localhost.local/ticket-system-mock-webapp:test-bundle`, the staging script
reuses that local image and does not try to pull it from a registry.

## 3. Start The Production-Style Local Test Stack

Start the staged deployment from the generated bundle:

```bash
scripts/setup_production_test_instance.bash

# or just the docker compose part if the bundle is already staged and .env is ready:
cd .tms-prod-test/ticket-system-mock-test-bundle
COMPOSE_PROJECT_NAME=ticket-system-mock-test-bundle docker compose -f docker-compose.yaml up -d
```

This script performs the following steps automatically:

1. stages the generated ZIP under `.tms-prod-test/`
2. writes a local `.env` file with generated secrets
3. pulls referenced images when needed
4. resets any previous stack state
5. starts the production-style Docker Compose stack
6. verifies management bootstrap completion
7. verifies the HTTPS entrypoint redirect
8. verifies admin login with `admin / admin1234`

Expected endpoint after startup:

```text
https://localhost:8443
```

## 4. Inspect The Running Stack Manually

The staged deployment directory is:

```text
.tms-prod-test/ticket-system-mock-test-bundle
```

Inspect the running services:

```bash
cd .tms-prod-test/ticket-system-mock-test-bundle
export COMPOSE_PROJECT_NAME=ticket-system-mock-test-bundle 
docker compose -f docker-compose.yaml -f docker-compose.override.yaml ps
docker compose -f docker-compose.yaml -f docker-compose.override.yaml logs --no-color management
docker compose -f docker-compose.yaml -f docker-compose.override.yaml logs --no-color webapp
docker compose -f docker-compose.yaml -f docker-compose.override.yaml logs --no-color nginx
```

Verify the HTTPS entrypoint manually:

```bash
curl -k -I https://localhost:8443/
```

Expected result:

- HTTP status `302`
- `Location: /accounts/login/?next=/`

Optional browser verification:

1. Open `https://localhost:8443/`.
2. Sign in with username `admin` and password `admin1234`.
3. Confirm that the home page loads after login.

## 5. Clean Up The Production Test Stack

Stop and remove the staged test stack:

```bash
cd /workspaces/itoperation-ticketing-demo-service/.tms-prod-test/ticket-system-mock-test-bundle
COMPOSE_PROJECT_NAME=ticket-system-mock-test-bundle docker compose -f docker-compose.yaml -f docker-compose.override.yaml down -v
```

Remove the staged deployment directory if you no longer need it:

```bash
cd /workspaces/itoperation-ticketing-demo-service/
rm -rf /workspaces/itoperation-ticketing-demo-service/.tms-prod-test
```

## 6. Troubleshooting

If the bundle is missing:

```bash
ls -1 build/deploy
```

If the management container does not finish successfully:

```bash
cd /workspaces/itoperation-ticketing-demo-service/.tms-prod-test/ticket-system-mock-test-bundle
docker compose -f docker-compose.yaml -f docker-compose.override.yaml logs --no-color management
```

If the web application does not respond after bootstrap:

```bash
docker compose -f docker-compose.yaml -f docker-compose.override.yaml logs --no-color webapp
docker compose -f docker-compose.yaml -f docker-compose.override.yaml logs --no-color nginx
```

If you want to rerun the full verification flow, go back to the repository root
and run the build and staging commands again. The staging script already resets
the previous stack state before starting a new one.