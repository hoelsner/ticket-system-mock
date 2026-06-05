# n8n Planning and Architecture

## Purpose

This guide explains the design decisions that should be made before writing a
custom n8n node.

For this project, the main goal is to keep the node aligned with the
**REST API** contract and the **Web Application** boundary.

## Table of Contents

- [Start with the project boundary](#start-with-the-project-boundary)
- [Prerequisites](#prerequisites)
- [Choose the node type](#choose-the-node-type)
- [Choose the implementation style](#choose-the-implementation-style)
- [Plan resources and operations](#plan-resources-and-operations)
- [Design the node UI](#design-the-node-ui)
- [Architecture checklist](#architecture-checklist)

## Start with the Project Boundary

Before choosing a node style, confirm that the node belongs outside the
**Web Application**.

In this repository:

- the **Web Application** owns issue lifecycle rules, permissions, and data
  integrity
- the **REST API** is the supported machine-facing contract
- the n8n node should call the API instead of reusing internal application code

That boundary matters because it keeps automation logic separate from the
system of record.

Do not design the node around direct database access, Django internals, or
duplicated workflow rules.

## Prerequisites

Before implementation, collect the following information:

- target **REST API** endpoints and methods
- authentication method and required credentials
- expected request and response shapes
- error responses that workflows must handle
- pagination, filtering, and rate-limit behavior
- the exact user outcome the workflow needs

If the upstream API design is still unstable, fix that first. A custom node is
easier to maintain when it sits on top of a stable contract.

## Choose the Node Type

The official n8n guidance distinguishes between action nodes and trigger nodes.

| Node Type | Use When | Project Guidance |
| --- | --- | --- |
| Action node | A workflow already has input and needs to create, fetch, update, or transition data. | This should be the default for REST API operations in this repository. |
| Trigger node | A workflow should start when an external event happens or when new data appears. | Use only when the workflow truly needs event or polling behavior. Keep the source of truth in the **Web Application**. |

For this project, most API-backed operations should start as action nodes.
Examples include:

- create an **Issue**
- fetch one or more **Issue** records
- update assignment or metadata on an **Issue**
- trigger an **Issue State Transition** through the API

Trigger nodes are appropriate only when n8n must start the workflow itself, for
example by polling the API for new records or receiving a webhook.

## Choose the Implementation Style

n8n supports declarative and programmatic node implementations.

| Style | Best For | Avoid When | Project Default |
| --- | --- | --- | --- |
| Declarative | Standard REST API resources, straightforward request mapping, low transformation needs | You need trigger behavior, non-REST protocols, external libraries, or full versioning | Prefer this first for action nodes against the project REST API |
| Programmatic | Trigger nodes, non-REST APIs, complex request or response handling, item transformation, full versioning | The logic is just a direct REST mapping | Use only when declarative style cannot express the behavior cleanly |

Use declarative style when the node mainly maps n8n parameters to REST API
requests.

Choose programmatic style when one or more of these are true:

- the node is a trigger node
- the API interaction is not standard REST behavior
- the node needs external dependencies
- the node must transform incoming items heavily before sending or returning data
- the node needs full versioning with separate implementation folders

If both approaches look possible, start with declarative style. It is easier to
review, easier to maintain, and closer to the default n8n recommendation for
REST-backed integrations.

## Plan Resources and Operations

Define the node around stable domain concepts instead of around individual HTTP
endpoints.

For this repository, use the project's canonical terms. Prefer names such as:

- **Issue**
- **Issue Comment**
- **Group**
- **Workflow State**

Avoid introducing alternative labels such as "ticket" or "team" when the API
and documentation already use canonical terms.

When designing resources and operations:

- map one resource to one recognizable API concept
- keep operation names verb-based and outcome-oriented
- reuse internal parameter names across operations when the value represents the
  same concept
- hide parameters that are irrelevant to the selected resource or operation
- decide early which fields are required and which belong under an advanced
  options section

## Design the Node UI

The n8n UI should simplify the API, not mirror every raw parameter.

Prefer this approach:

1. Expose the smallest set of fields needed for the common workflow.
2. Use conditional visibility so only relevant fields appear.
3. Move uncommon parameters into collections or additional options.
4. Use labels and descriptions that explain the business outcome, not only the
   transport detail.

Useful UI design rules from the official guidance:

- use `displayOptions` to keep the form focused
- avoid showing several fields with the same purpose at the same time
- choose specialized element types when they improve validation or selection
- use notices or hints when a workflow author must understand a constraint

Common field choices:

| UI Need | Preferred Element |
| --- | --- |
| short text value | string |
| numeric value | number |
| one choice from a fixed set | options |
| multiple choices from a fixed set | multi-options |
| grouped advanced settings | collection or fixed collection |
| raw structured payload | json |
| searchable identifier selection | resource locator |
| contextual warning or explanation | notice |

## Architecture Checklist

Before implementation, confirm all of the following:

- the node uses the **REST API** instead of internal application code
- the chosen node type matches the workflow entry point
- declarative style was ruled out before choosing programmatic style
- resource and operation names follow the project's canonical language
- the node UI is simplified for the common workflow path
- credentials and versioning needs are known before coding starts

## Related References

- [Implementation Reference](implementation-reference.md)
- [Testing and Distribution](testing-and-distribution.md)
- [n8n Plan a Node](https://docs.n8n.io/integrations/creating-nodes/plan/)
- [n8n Choose Declarative or Programmatic Style](https://docs.n8n.io/integrations/creating-nodes/plan/choose-node-method/)