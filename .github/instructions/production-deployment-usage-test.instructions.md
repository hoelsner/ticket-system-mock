---
description: "Use when building a production-style deployment bundle, staging the local production test instance, validating access, running scenario or SDK usage tests against that instance, or tearing the stack down."
name: "Production Deployment And Usage Test"
---

# Production Deployment And Usage Test

- For a fresh production-style local deployment, prefer the supported repository workflow from the repository root:
  - `IMAGE_REPOSITORY=localhost.local/ticket-system-mock-webapp deploy/build_scripts/build_environment.bash test-bundle`
  - `scripts/setup_production_test_instance.bash`
- The staging script expects the default bundle path `build/deploy/ticket-system-mock-test-bundle.zip`, creates `.tms-prod-test/ticket-system-mock-test-bundle`, starts the compose stack, and verifies the HTTPS entrypoint plus admin login.
- Default production-style access is `https://localhost:8443/` with bootstrap credentials `admin` / `admin1234`.
- For a cheap access check, use `curl -k -I https://localhost:8443/` and expect `302` with `Location: /accounts/login/?next=/`.
- When running SDK-based or scenario-based usage tests from the dev container, do not assume the stock Python SDK or scenario CLI can talk to the production test instance unchanged:
  - `https://localhost:8443` uses a self-signed certificate, and the SDK verifies TLS by default.
  - Direct container IP access is rejected by Django host validation unless the staged `.env` is updated accordingly, for example by extending `DJANGO_ALLOWED_HOSTS` beyond `localhost,127.0.0.1`.
- Prefer one of these local-only test paths instead of changing application code:
  - Run the usage test from inside the application network against `http://webapp:8000`.
  - Or inject a custom `httpx.Client` with `verify=False` and `follow_redirects=True` when using `TicketSystemClient` against `https://localhost:8443`.
- For the `issue-triage-with-n8n` scenario:
  - Refresh the dedicated environment with `cd scenarios && uv sync --python 3.14`.
  - Use the existing seed logic with a superuser account.
  - Expect the seed to reset the instance while preserving the authenticated superuser.
- After a successful production usage test, tear the instance down with:
  - `cd .tms-prod-test/ticket-system-mock-test-bundle`
  - `COMPOSE_PROJECT_NAME=ticket-system-mock-test-bundle docker compose -f docker-compose.yaml -f docker-compose.override.yaml down -v`
  - `rm -rf /workspaces/itoperation-ticketing-demo-service/.tms-prod-test`