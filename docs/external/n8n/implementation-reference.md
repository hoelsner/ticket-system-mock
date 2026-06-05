# n8n Implementation Reference

## Purpose

This guide summarizes the practical implementation details for custom n8n nodes
in this repository.

Use it after the planning decisions are already made.

## Table of Contents

- [Development environment](#development-environment)
- [Recommended package structure](#recommended-package-structure)
- [Base node metadata](#base-node-metadata)
- [Codex metadata](#codex-metadata)
- [Credentials files](#credentials-files)
- [UI element selection](#ui-element-selection)
- [Code standards](#code-standards)
- [Error handling](#error-handling)
- [Versioning](#versioning)
- [Paired items and item linking](#paired-items-and-item-linking)
- [Project guidance](#project-guidance)

## Development Environment

Follow the current n8n node-development guidance for the active n8n version.
In practice this means:

- use TypeScript for the node package
- use the official node tooling, including `n8n-node`, when scaffolding,
  checking, or linting the package
- keep the package compatible with the n8n version that will run it
- test the package in a local n8n instance before treating the work as done

When the package is only for internal use, keep the setup simple. Do not add
extra libraries unless the node behavior truly requires them.

## Recommended Package Structure

The exact file layout can vary, but the package should remain easy to review.
This is a useful baseline structure:

```text
src/n8n_node/
├── package.json
├── tsconfig.json
├── credentials/
│   └── ProjectApi.credentials.ts
├── nodes/
│   └── ProjectApi/
│       ├── ProjectApi.node.ts
│       └── ProjectApi.node.json
└── README.md
```

Use separate folders when versioning or node count makes the package harder to
navigate.

Keep one integration target per package unless there is a strong reason to mix
multiple third-party services.

## Base Node Metadata

Every node needs a clear description object or equivalent metadata.
At minimum, define:

- stable internal `name`
- human-facing `displayName`
- `description`
- `version`
- `inputs` and `outputs`
- `credentials`
- `properties`

For declarative nodes, keep request routing readable. Prefer explicit request
defaults and clear per-operation routing instead of deeply nested conditionals.

For programmatic nodes, keep the `execute` logic or trigger logic small enough
that each branch remains understandable.

## Codex Metadata

n8n also uses codex metadata files for documentation and package metadata.

Keep these values aligned with the real package state:

- node identifier
- node version
- codex version
- category and documentation metadata if required by the package format

When the node version changes, update the codex metadata in the same change.

## Credentials Files

Credentials should define authentication once and keep secrets out of normal
node properties.

A typical credentials file includes:

- internal `name`
- `displayName`
- `documentationUrl`
- credential `properties`
- `authenticate` behavior
- optional `test` request

Project guidance:

- keep credential names specific to the target API
- model fields around the real authentication flow, such as base URL, username,
  password, token, or header value
- add a test request when the remote API makes that possible
- do not duplicate credential input as normal node fields

## UI Element Selection

Choose UI elements that reduce user error and simplify the workflow authoring
experience.

| Use Case | Element Type | Guidance |
| --- | --- | --- |
| free-form identifier or label | string | Use for simple text values with clear descriptions. |
| count, limit, timeout | number | Use when numeric validation matters. |
| controlled enum-like input | options | Prefer this over free text when the set is stable. |
| many toggles or grouped expert settings | collection or fixed collection | Keep the main form short. |
| raw JSON payload | json | Only expose this when structured input is truly needed. |
| searchable record selection | resource locator | Useful when workflows should select a remote object interactively. |
| explanatory message | notice | Use for constraints, prerequisites, or warnings. |

If two operations represent the same conceptual input, reuse the same internal
parameter name so user values survive resource or operation switching.

## Code Standards

The official n8n guidance emphasizes a few standards that are especially useful
here:

- keep the package in TypeScript
- prefer declarative implementation for straightforward REST API actions
- use n8n's built-in request helpers instead of ad hoc HTTP code where possible
- do not mutate incoming items in programmatic nodes
- keep internal parameter names stable across related operations
- use conditional visibility instead of duplicating the same field in many forms

Treat the node as a thin integration layer. If the logic starts to look like a
second business-logic implementation, move that behavior back behind the
**REST API**.

## Error Handling

Use the standard n8n error types instead of generic exceptions.

| Situation | Preferred Error |
| --- | --- |
| Invalid user input or unsupported combination of parameters | `NodeOperationError` |
| Remote API returned an error response | `NodeApiError` |

When processing multiple items in a programmatic node, attach the correct
`itemIndex` so n8n can report which input item failed.

Error messages should explain the user-visible problem, not only the internal
implementation detail.

## Versioning

n8n supports multiple versioning approaches.

| Versioning Style | Use When | Notes |
| --- | --- | --- |
| Light versioning | Small additive changes to fields or behavior | Good default for incremental improvements. |
| Feature-based versioning | Larger feature additions that still fit one implementation shape | Use when a node evolves but does not need a full rewrite. |
| Full versioning | Breaking redesign, major execution changes, or version-isolated implementations | Declarative nodes do not support full versioning. Use version folders for programmatic nodes. |

Pick the smallest versioning model that keeps upgrades safe.

## Paired Items and Item Linking

Declarative nodes usually get item linking support automatically.

Programmatic nodes and trigger nodes need more care. Preserve the relationship
between each output item and the input item that produced it so downstream n8n
expressions continue to work.

If one input produces many outputs, design the paired-item mapping explicitly.

## Project Guidance

For this repository, keep the implementation aligned with the domain language
already used by the **Web Application** and the **REST API**.

- prefer resource names such as **Issue** and **Group**
- avoid alias terms such as "ticket" or "team"
- expose workflow actions in terms of the API contract, not hidden internal rules
- keep the node package focused on transport, mapping, validation, and error
  reporting

## Related References

- [Planning and Architecture](planning-and-architecture.md)
- [Testing and Distribution](testing-and-distribution.md)
- [n8n Build a Node](https://docs.n8n.io/integrations/creating-nodes/build/)
- [n8n Build Reference](https://docs.n8n.io/integrations/creating-nodes/build/reference/)