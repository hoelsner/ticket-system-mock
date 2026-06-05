---
description: "Use when accessing, verifying, or troubleshooting the running development server, background webapp service, browser checks, or static asset delivery in the workspace."
---

When working with the running development server in this repository, follow these rules:

## Access and Hostnames

- prefer `http://webapp:8000` from inside the dev container for HTTP checks, browser automation, and service-to-service access
- do not assume `http://localhost:8000` is reachable from inside the dev container; verify it before using it
- when checking redirects from the root page, expect unauthenticated requests to redirect to `/accounts/login/?next=/`

## Background Development Server

- assume the development server is already running in the background unless there is evidence that it is unavailable
- restart the background webapp service with `make webapp-restart-devserver` when server-side code or runtime state appears stale
- use `docker compose logs webapp` to confirm startup, inspect tracebacks, and diagnose wrong behavior in the running service

## Static Asset Verification

- verify static assets with direct HTTP requests against the running service, for example `curl -I http://webapp:8000/static/...`
- if a rendered page references `/static/...` but the asset returns `404`, inspect Django staticfiles configuration before changing templates or vendored assets
- for project-level static assets under `src/webapp/static`, ensure Django is configured to discover that directory instead of assuming app-local static directories are the only source

## Browser and Playwright Checks

- use the available Playwright tool when browser-level verification is needed
- when Playwright is unavailable or blocked, fall back to direct HTTP verification and rendered HTML inspection to isolate whether the issue is browser-side or server-side
- treat browser console errors separately from server delivery problems; for example, missing favicons and COOP warnings are not the same as failed stylesheet delivery

## Use of the System

- the superuser account is pre-configured with the username `admin` and password `admin1234`, you can use this account to log in to the user and admin interface

## Troubleshooting Sequence

- first confirm the target URL is reachable from the current environment
- then confirm the rendered HTML references the expected asset or route
- then verify the referenced URL returns the expected HTTP status and content type
- only after those checks should you change Django settings, templates, or static asset placement