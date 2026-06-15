---
description: "Use when performing large changes to the codebase, such as refactors, feature additions, or bug fixes that span multiple files. These guidelines help ensure changes are well-scoped, assumptions are surfaced, and success criteria are defined for effective verification."
---

# Codebase Verification Guidelines

- When making large changes to the codebase, such as refactors, feature additions, or bug fixes that span multiple files, follow these guidelines to ensure your changes are well-scoped, assumptions are surfaced, and success criteria are defined for effective verification.
- run the `make check` command frequently during development to catch linting errors and test failures early, ideally after completing each logical task or change.
- run the `make test` command after completing a set of related changes to ensure that all tests pass and to generate a coverage report, which can help identify untested code paths and verify that your changes are adequately tested.
- invoke repository-level `make` targets from the repository root. If your shell
	is currently inside a subdirectory, prefer `make -C /workspaces/itoperation-ticketing-demo-service check`
	and `make -C /workspaces/itoperation-ticketing-demo-service test` so the
	intended top-level targets are used consistently.
- if `make check` fails late in the pipeline, rerun the exact failing target or the narrow failing command first, for example `make -C /workspaces/itoperation-ticketing-demo-service webapp-unittest`, `make -C /workspaces/itoperation-ticketing-demo-service n8n-node-lint`, or a single `python3 manage.py test ... --keepdb` invocation, and only rerun the full repository target after the local blocker is fixed.
- for Django test debugging, prefer targeted `python3 manage.py test ... --keepdb` commands from `src/webapp` because the wrapper scripts intentionally suppress successful output and the full suite is comparatively expensive to rerun.
- if the change set includes YAML configuration or customization files,
	validate those files explicitly as part of the same verification pass because
	tab indentation can break repository validation before the main tests run.
- if validated changes affect the local integration surfaces used by the development environment, finish with `make -C /workspaces/itoperation-ticketing-demo-service update-devserver` after the check and test targets are green so staged SDK and n8n artifacts match the current source tree.