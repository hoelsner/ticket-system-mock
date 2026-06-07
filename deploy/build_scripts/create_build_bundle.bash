#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
compose_template="$repo_root/deploy/docker-compose/docker-compose-template.yaml"
compose_override_template="$repo_root/deploy/docker-compose/docker-compose.template.override.yaml"
user_docs_dir="$repo_root/docs/user"
output_root="${BUNDLE_OUTPUT_DIR:-$repo_root/build/deploy}"

build_version="${1:-${BUILD_VERSION:-}}"
image_ref="${2:-${IMAGE_REF:-}}"
commit_id="${3:-${COMMIT_ID:-unknown}}"

if [[ -z "$build_version" ]]; then
	echo "usage: $0 <build-version> <image-ref> [commit-id]"
	exit 1
fi

if [[ -z "$image_ref" ]]; then
	echo "image reference is required"
	exit 1
fi

if [[ ! -f "$compose_template" ]]; then
	echo "docker compose template not found at $compose_template"
	exit 1
fi

if [[ ! -f "$compose_override_template" ]]; then
	echo "docker compose override template not found at $compose_override_template"
	exit 1
fi

if [[ ! -d "$user_docs_dir" ]]; then
	echo "user documentation directory not found at $user_docs_dir"
	exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
	echo "zip is required to create the deployment archive"
	exit 1
fi

archive_basename="ticket-system-mock-$build_version"
bundle_dir="$output_root/$archive_basename"
bundle_zip="$output_root/$archive_basename.zip"

rm -rf "$bundle_dir"
mkdir -p "$bundle_dir"

cp "$compose_template" "$bundle_dir/docker-compose.yaml"
cp "$compose_override_template" "$bundle_dir/docker-compose.override.yaml"
mkdir -p "$bundle_dir/docs/user"
cp "$user_docs_dir/README.md" "$bundle_dir/docs/user/README.md"
cp "$user_docs_dir/product-overview.md" "$bundle_dir/docs/user/product-overview.md"
cp "$user_docs_dir/configuration.md" "$bundle_dir/docs/user/configuration.md"

cat >"$bundle_dir/.env.example" <<EOF
# Docker Compose deployment defaults for Ticket System Mock
# WEBAPP_IMAGE is intentionally omitted here.
# docker-compose.yaml already defaults to the published image.
DJANGO_SECRET_KEY=change-me
SERVICE_BASE_URL=https://localhost:8443
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_TIME_ZONE=UTC
POSTGRES_DB=itoticketing
POSTGRES_USER=itoticketing
POSTGRES_PASSWORD=change-me
CACHE_PASSWORD=change-me
NGINX_SERVER_NAME=localhost
NGINX_HTTP_PORT=8080
NGINX_HTTPS_PORT=8443
EOF

cat >"$bundle_dir/build-metadata.env" <<EOF
BUILD_VERSION=$build_version
BUILD_COMMIT_ID=$commit_id
WEBAPP_IMAGE=$image_ref
EOF

cat >"$bundle_dir/DEPLOYMENT.md" <<EOF
# Deployment Bundle

This bundle was generated from commit $commit_id for build version $build_version.

## Files

- docker-compose.yaml: production compose stack
- docker-compose.override.yaml: optional local overrides
- .env.example: environment template with the built image reference
- build-metadata.env: generated build metadata

## Quick Start

1. Copy .env.example to .env and replace the placeholder secrets.
2. The compose template already defaults to the published Docker Hub image hoelsner/ticket-system-mock:latest.
3. Review docker-compose.override.yaml and remove it if not needed.
4. Adjust SERVICE_BASE_URL, DJANGO_ALLOWED_HOSTS, NGINX_SERVER_NAME, and the published ports when you are deploying to a non-local hostname or different host ports.
5. Start the stack with docker compose -f docker-compose.yaml up -d.
EOF

cat >"$bundle_dir/SETUP_AND_CONFIGURATION.md" <<EOF
# Setup and Configuration Guide

This guide is generated as part of build version $build_version from commit $commit_id.
It summarizes the current product and configuration documentation shipped with the repository.

## Product Summary

Ticket System Mock is a lightweight ticketing system for demos,
workflow simulations, and integration scenarios. It provides:

- an authenticated user frontend with issue workflows and a Kanban board
- a Django Admin surface for operational and branding data
- a REST API for integrations and automation scenarios

## Bundle Contents

- docker-compose.yaml starts the production-style stack
- docker-compose.override.yaml is an optional override file
- .env.example contains the main runtime variables to copy into .env
- docs/user/ contains the bundled user documentation used as the source for this guide

## Runtime Layout

The production image keeps application code under /app and expects the shared
runtime volume to be mounted at /runtime.

The runtime volume stores:

- collected static files under /runtime/static
- uploaded media under /runtime/media
- generated certificates under /runtime/certificates
- provisioning state under /runtime/provisioning
- generated NGINX configuration under /runtime/nginx

Database data and Redis data are stored in their own named Docker volumes.

## Deployment Steps

1. Copy .env.example to .env.
2. The compose template already defaults to the published Docker Hub image hoelsner/ticket-system-mock:latest.
3. Replace the placeholder values for DJANGO_SECRET_KEY, POSTGRES_PASSWORD, and CACHE_PASSWORD.
4. Adjust SERVICE_BASE_URL, DJANGO_ALLOWED_HOSTS, NGINX_SERVER_NAME, and the published ports when you are deploying to a non-local hostname or different host ports.
5. Start the stack with docker compose -f docker-compose.yaml up -d.
6. Check docker compose -f docker-compose.yaml logs management until migrations and provisioning finish.

## Main Configuration Variables

| Environment Variable | Default Value | Used For |
| --- | --- | --- |
| DJANGO_DEBUG | False in the compose template | Enables or disables Django debug mode. |
| DJANGO_SECRET_KEY | change-me in the compose template | Sets Django's secret key. |
| SERVICE_BASE_URL | https://localhost:8443 | Defines the canonical externally exposed base URL that API consumers can prepend to relative REST API URLs such as attachment download paths. |
| DJANGO_ALLOWED_HOSTS | localhost,127.0.0.1 | Sets the allowed hosts list as a comma-separated value. |
| DJANGO_TIME_ZONE | UTC | Sets the Django application time zone. |
| DJANGO_LOG_LEVEL | INFO | Sets the Django log level written to stdout. |
| PRODUCT_DISPLAY_NAME | Ticket System Mock | Provides the default product name used by the frontend and admin. |
| POSTGRES_DB | itoticketing | Sets the PostgreSQL database name. |
| POSTGRES_USER | itoticketing | Sets the PostgreSQL user name. |
| POSTGRES_PASSWORD | PlsChgMePostgres | Sets the PostgreSQL password. Override this in production. |
| POSTGRES_HOST | database | Sets the PostgreSQL host used by the web application. |
| POSTGRES_PORT | 5432 | Sets the PostgreSQL port used by the web application. |
| CACHE_PASSWORD | PlsChgMeCache | Sets the Redis password. Override this in production. |
| CACHE_HOST | cache | Sets the Redis host used by the cache configuration. |
| CACHE_PORT | 6379 | Sets the Redis port used by the cache configuration. |
| CACHE_DB | 0 | Sets the Redis database index used by the cache configuration. |
| NGINX_SERVER_NAME | localhost | Sets the NGINX server_name value used by the generated reverse proxy config. |
| NGINX_HTTP_PORT | 8080 | Publishes the HTTP port on the host. |
| NGINX_HTTPS_PORT | 8443 | Publishes the HTTPS port on the host. |

## Branding Notes

Runtime branding is split between environment configuration and admin-managed media assets.

- PRODUCT_DISPLAY_NAME provides the fallback product name for the application.
- Django Admin can override the display name and upload a custom navbar logo and login background image.
- Uploaded branding assets are stored under /runtime/media and should be treated as persistent runtime content.

## Included Reference Docs

- docs/user/README.md
- docs/user/product-overview.md
- docs/user/configuration.md
EOF

rm -f "$bundle_zip"

(
	cd "$output_root"
	zip -rq "$bundle_zip" "$archive_basename"
)

echo "bundle directory: $bundle_dir"
echo "bundle archive: $bundle_zip"
#