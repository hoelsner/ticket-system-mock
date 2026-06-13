---
description: This file describes the coding style and best practices for the project
# apply to python, html, js, css files in the src/webapp directory
applyTo: src/webapp/**/*.{py,html,js,css}
---

When developing code, use the following workflow to ensure that your code is clean, maintainable, and adheres to the project's standards:

## Development Workflow

1. Understand the problem and desired outcome

- If you see a potential improvement, mention it - don't implement it without confirmation.

2. Collect all relevant information and clarify any ambiguities with the user

- If you need additional information, look at `docs/architecture` and `docs/external`
- If you notice a bug, mention it - don't fix it without confirmation.
- If the task involves building or restyling frontend screens in `src/webapp`, use the `frontend-design` skill so the visual direction stays deliberate while still following the repository's Pico CSS, Django Cotton, HTMX, dark-mode, and i18n rules.

3. Break down the problem into smaller, manageable tasks
4. based on the karpathy-guidelines, write clean, modular code that follows the project's style and guidelines
5. Test your code thoroughly, including edge cases and error handling
6. after each task, run the following commands to check for linting errors and run tests:

```bash
make check
```

Run repository-level `make` targets from the repository root. If your current
working directory drifted into a subdirectory such as `src/webapp` or
`src/n8n_node`, use `make -C /workspaces/itoperation-ticketing-demo-service …`
instead of assuming the local directory has the same targets.

If you encounter errors, fix them before proceeding to the next task.

7. after completing all tasks, run the following command to check for linting errors, run tests, and generate a coverage report:

```bash
make check
make test
```

If you encounter errors, fix them before proceeding to the next step.

8. Document your code and any important decisions or assumptions
9. check for documentation drift and update the documentation if needed
10. check for common patterns and guidelines and update the instructions if needed

- for REST API changes in `src/webapp`, update the Django Ninja metadata that
  feeds `/api/docs` and `/api/openapi.json` in the same change set; this
  includes endpoint summaries, descriptions, tags, query parameter
  descriptions, request payload attributes, and response schema field
  descriptions
- for machine-facing contract changes that affect the bundled n8n package,
  update the corresponding files under `src/n8n_node`, rebuild the committed
  `dist/` output, and refresh the n8n-facing docs in the same change set

## Common Principles

- avoid unnecessary abstractions and complexity; prefer simple, direct solutions that are easy to understand and maintain
- avoid duplicated knowledge; if you find yourself copying and pasting code or explanations, consider whether there is a better way to structure the code or documentation to keep the information in one place
- for all user-facing webapp work, treat localization as the default: templates, form labels, help text, model field metadata, choice labels, validation messages, and other UI copy must use Django i18n APIs and be added to the locale catalogs in the same change set
- maintain release-build configuration variables in `deploy/docker-compose/docker-compose-template.yaml` as the primary runtime source, keep `docs/user/configuration.md` aligned with those variables, and use the Dockerfile only for stable non-secret container defaults and build metadata
- for frontend design work, let visual distinctiveness come from a single held design direction and disciplined tokens, not from fabricated data, filler copy, or themed replacements for standard UI labels
- for frontend styling in `src/webapp`, keep color treatment close to Pico CSS by default; avoid adding tinted gradients, blurred color washes, or custom background colorization unless the user explicitly asks for a stronger visual departure
- when a webapp domain module becomes crowded, prefer a package with one class per file for models and controllers rather than continuing to grow a single large module
- keep package-level compatibility imports in `__init__.py` when splitting Django models or controllers so existing admin, signal, test, and migration imports remain stable
- do not modify the code related to complexity or linting, if you think a change is needed, mention it first and wait for confirmation before making any changes to the codebase
- if you run into complexity violations, refactor the code to reduce complexity while preserving behavior, and then update the instructions to prevent similar issues in the future
- for REST API work, treat `/api/docs` and `/api/openapi.json` as maintained deliverables, not incidental output; add or update OpenAPI-focused tests when changing endpoint purpose or payload shape
- for YAML configuration and customization files, use spaces only; tabs can make
  files fail validation even when the content is otherwise correct