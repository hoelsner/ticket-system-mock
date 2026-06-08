---
description: "Use when creating, resetting, or verifying a production-style test instance under .tms-prod-test, especially for bundle staging, port 8443 access, or admin login validation."
name: "Production Test Instance"
---

# Production Test Instance

- Prefer `scripts/setup_production_test_instance.bash` when the task is to stand up a production-style local instance from a generated deployment bundle or from the default published image path.
- The script stages the deployment bundle under `.tms-prod-test/`, writes the local `.env`, resolves `WEBAPP_IMAGE` from `build-metadata.env` when present, falls back to `WEBAPP_IMAGE` from the environment when provided, then defaults to `hoelsner/ticket-system-mock:latest`.
- When `WEBAPP_IMAGE` points at a local-only tag such as `localhost.local/...`, the script skips pulling that webapp image and still pulls the supporting images.
- The script starts the compose stack and validates the HTTPS entrypoint plus admin login.
- Default host ports are `8080` for HTTP and `8443` for HTTPS.
- The default verification path is `https://localhost:8443/` and the predefined admin credentials are `admin` / `admin1234`.
- If the task is specifically about the published image path, keep the default image resolution unless the user explicitly asks to validate a locally built image bundle.