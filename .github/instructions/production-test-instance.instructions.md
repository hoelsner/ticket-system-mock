---
description: "Use when creating, resetting, or verifying a production-style test instance from the published Docker Hub image, especially for .tms-prod-test staging, port 8443 access, or admin login validation."
name: "Production Test Instance"
---

# Production Test Instance

- Prefer `scripts/setup_production_test_instance.bash` when the task is to stand up a production-style local instance from the published Docker Hub image.
- The script stages the deployment bundle under `.tms-prod-test/`, writes the local `.env`, mounts a replacement management script required by the current published image, pulls images, starts the compose stack, and validates HTTPS plus admin login.
- Default host ports are `8080` for HTTP and `8443` for HTTPS.
- The default verification path is `https://localhost:8443/` and the predefined admin credentials are `admin` / `admin1234`.
- If the task is specifically about the published image path, do not switch to the local image build workflow unless the user asks for it.