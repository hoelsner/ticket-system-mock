# n8n Testing and Distribution

## Purpose

This guide explains how to validate a custom n8n node locally and how to decide
between private and community distribution.

## Table of Contents

- [Local validation workflow](#local-validation-workflow)
- [Validation tooling](#validation-tooling)
- [Suggested test scenarios](#suggested-test-scenarios)
- [Troubleshooting](#troubleshooting)
- [Private installation](#private-installation)
- [Community distribution](#community-distribution)
- [Project release guidance](#project-release-guidance)

## Local Validation Workflow

Validate the node in the same order that a workflow author will use it.

1. Build the node package and confirm the TypeScript output is current.
2. Install or link the package into a local n8n instance.
3. Configure credentials and confirm the credential test passes.
4. Exercise each resource and operation with realistic API responses.
5. Verify error handling with invalid input and remote failures.
6. Verify multi-item behavior and output mapping.
7. Re-run the workflow after changing parameters to confirm field visibility and
   defaults still behave correctly.

For internal development, keep a local n8n environment that can call the
project **REST API** safely.

## Validation Tooling

Use the official n8n tooling as part of the validation flow.

- use `n8n-node` and the related linting workflow when checking package shape
  and node conventions
- use the community-package scan before any public release candidate
- treat tooling failures as design feedback, not only as release blockers

For internal-only development, not every community check is mandatory, but the
package should still be lint-clean and structurally sound before it is shared.

## Suggested Test Scenarios

At minimum, test the following:

- valid authentication
- invalid authentication
- missing required fields
- not-found responses from the remote API
- validation errors returned by the API
- pagination or repeated fetch behavior
- multiple input items in one run
- trigger re-entry or duplicate detection if the node is a trigger

When the node performs **Issue State Transition** actions, include tests for the
allowed and rejected state changes that the **REST API** exposes.

## Troubleshooting

If the node does not appear or behave as expected, check these areas first:

- the package was built after the latest source change
- the local n8n instance is loading the correct custom-node directory
- credentials names match the node metadata exactly
- codex and node version values are still aligned
- conditional field visibility is not hiding a required input unexpectedly
- the node is using standard n8n error types instead of opaque thrown errors

For local custom-node testing, create the standard n8n custom-node directory if
it does not exist yet.

## Private Installation

Private installation is the default path for this repository unless there is a
clear requirement to publish externally.

Use private distribution when:

- the node is tightly coupled to this project's **REST API**
- the node is intended for one controlled n8n deployment
- the package includes project-specific assumptions that are not useful for the
  broader n8n community

Before private installation:

- confirm the target n8n version
- confirm the target **REST API** version or contract state
- document required credentials and base URL settings
- confirm that the package build artifact is reproducible

## Community Distribution

If the node may later become a community package, design toward the stricter
constraints early.

The official guidance for community and verified nodes includes requirements
such as:

- one third-party service per package
- MIT license for verified-node eligibility
- TypeScript implementation
- passing the official package scan and linting steps
- English-language documentation
- published package provenance

Verified-node guidance also discourages or disallows patterns such as:

- unnecessary external dependencies
- direct environment-variable access inside the node package
- file-system access from the node package

Treat these as optional future requirements unless the package is meant for
public publication.

## Project Release Guidance

Coordinate node changes with the **REST API** contract.

When a change in the **Web Application** affects request shapes, response
shapes, authentication, or available operations:

- update the node package
- update the relevant local documentation in this directory
- decide whether the node version also needs to change
- retest the workflows that depend on the changed operation

If the node stays private, keep the release notes simple. Focus on supported
operation changes and compatibility expectations between n8n and the project
**REST API**.

## Related References

- [Planning and Architecture](planning-and-architecture.md)
- [Implementation Reference](implementation-reference.md)
- [n8n Test Nodes](https://docs.n8n.io/integrations/creating-nodes/test/)
- [n8n Deploy Nodes](https://docs.n8n.io/integrations/creating-nodes/deploy/)