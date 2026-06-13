# Coding and Documentation Standards

## Purpose

This guide defines the baseline standards contributors should follow when
writing code and maintaining documentation in this repository.

## Core Principles

### Prefer clear code over explanatory comments

Write code that is easy to read, test, and maintain. Use descriptive names,
small functions, and clear module boundaries so comments are only needed where
intent would otherwise be hard to infer.

### Avoid duplicated knowledge

Keep behavior, rules, and explanations in one authoritative place. If code or
documentation must be updated in multiple places for one change, treat that as a
design smell.

### Document decisions, not the obvious

Comments and documentation should explain intent, constraints, tradeoffs, and
non-obvious behavior. Avoid comments that only restate what the code already
shows.

### Write for the primary reader

Use contributor-facing documentation for setup, workflow, testing, and
maintenance guidance. Use user or architecture docs for product behavior and
system design instead of mixing audiences in one document.

## Coding Standards

- Use descriptive names for variables, functions, classes, files, and modules.
- Keep functions focused on one task.
- Organize code into logical layers with clear responsibilities.
- Keep Django domain entities and business rules in `djangoapp.core`.
- Keep machine-facing REST API views and URL wiring in `djangoapp.rest_api`.
- Keep authenticated HTML views and UI URL wiring in `djangoapp.user_interface`.
- Allow `djangoapp.rest_api` and `djangoapp.user_interface` to depend on
  `djangoapp.core`, but do not move UI or API surface code back into
  `djangoapp.core`.
- Implement business logic for each entity in dedicated controller classes.
- Use the structural flow `view -> controller -> model` for frontend page
  behavior.
- Use the structural flow `view -> form -> controller -> model` for frontend
  form handling.
- Use the structural flow `signal -> controller` for model-instance event
  handling.
- Use the structural flow `REST API view -> controller -> model` for API
  behavior.
- Treat light mode and dark mode support as required behavior for both the user
  frontend and the admin frontend.
- Treat multilingual support as a whole-application requirement and implement
  it with Django's built-in internationalization system.
- Treat the authentication experience as a split-layout view with a functional
  left panel and a contextual right-side illustration.
- Treat the authenticated user experience as a top-down application shell with
  persistent top navigation, a left burger menu for detailed navigation, a
  top-right utility area, and a main content region for task-specific views.
- Follow the existing formatter, linter, and project conventions for the
  language being changed.
- Handle errors consistently and make failure modes easy to understand.
- do not add ignore verdicts for coverage (e.g. #cov-ignore) without any explicit confirmation from the user, if you think an ignore verdict is needed, mention it first and wait for confirmation before adding it to the codebase
- do not add ignore verdicts for bandit (e.g. #nosec) without confirmation, if you think a bandit ignore verdict is needed, mention it first and wait for confirmation before adding it to the codebase

## Documentation Standards

- Keep documentation concise, accurate, and close to the code or process it
  describes.
- Update documentation in the same change set as the code when behavior,
  configuration, or workflows change.
- When a REST API contract changes, update the Swagger or OpenAPI metadata in
  the same change so `/api/docs` and `/api/openapi.json` still describe the
  endpoint purpose, request payloads, and schema fields.
- Prefer practical project-specific guidance over copied vendor or marketing
  material.
- Split mixed-content documents by dominant audience when needed.
- Use examples, short lists, and diagrams only when they make the document
  easier to act on.

## Review Expectations

Documentation quality is part of code review. Reviewers should check whether:

- new behavior is documented where needed
- existing docs still match the implementation
- names and terminology are consistent
- comments explain intent rather than repeating code

## Mandatory Workflow

1. Make the code change.
2. Update the relevant tests or validation steps.
3. Update developer, user, or architecture documentation if the change affects
  behavior, operation, or design.
4. If the change affects the REST API, review `/api/docs` and `/api/openapi.json`
  and update the generated documentation inputs in `djangoapp.rest_api.api`.
5. Review the result for duplicated or outdated explanations.

If the webapp was changed, verify the n8n node implementation and extend them if needed.

## Repository-Specific Guidance

- Keep contributor guidance in `docs/development/`.
- Keep system structure and deployment design in `docs/architecture/`.
- Keep dependency- and framework-specific reference material in `docs/external/`.
- Keep product usage and workflow explanations in `docs/user/`.