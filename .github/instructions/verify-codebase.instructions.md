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
- if the change set includes YAML configuration or customization files,
	validate those files explicitly as part of the same verification pass because
	tab indentation can break repository validation before the main tests run.