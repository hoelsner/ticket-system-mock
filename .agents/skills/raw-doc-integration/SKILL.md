---
name: raw-doc-integration
description: 'Integrate source documents from .raw into the project documentation. Use when importing, classifying, rewriting, or placing raw markdown into docs/development, docs/architecture, docs/external, or docs/user.'
argument-hint: 'Describe which .raw files to integrate and whether to classify only or also rewrite and place them'
disable-model-invocation: true
user-invocable: true
---

# Raw Document Integration

## What This Skill Does

This skill turns individual source documents from `.raw/` into project documentation that fits the repository structure and documentation intent.

It helps with three things:

1. Decide the correct destination area: `development`, `architecture`, `external`, or `user`.
2. Rewrite the source so it matches the target audience and documentation purpose.
3. Place the document into the appropriate docs subtree and note follow-up work such as nav updates or cross-links.

## When to Use

Use this skill when:

- `.raw/` contains source markdown that should become part of the maintained project docs.
- a document mixes product, implementation, deployment, or dependency details and needs classification.
- you need a repeatable way to decide whether content belongs in developer docs, architecture docs, external reference docs, or user-facing docs.

## Documentation Areas

Use these rules to classify each document.

### `docs/development/`

Choose this area for contributor-facing material about how to build, run, test, debug, or maintain the project.

Typical signals:

- local setup
- development workflow
- QA steps
- coding conventions
- release or delivery process
- contributor instructions

### `docs/architecture/`

Choose this area for system structure and runtime design.

Typical signals:

- component boundaries
- deployment topology
- container or service roles
- data flow
- ownership boundaries
- architectural decisions and tradeoffs

### `docs/external/`

Choose this area for third-party technologies, APIs, and dependency-specific reference material.

Typical signals:

- framework usage guidance
- external APIs or integration contracts
- library-specific best practices
- vendor or ecosystem reference notes

Move it to the appropriate docs subtree if it mainly serves as a reference for a specific dependency or platform used by the project, rather than general architectural or user-facing guidance.

### `docs/user/`

Choose this area for product behavior and user-facing workflows.

Typical signals:

- feature overview
- end-user or operator tasks
- screen or workflow explanations
- product concepts and capabilities
- usage-oriented configuration guidance

## Procedure

1. Read the requested files from `.raw/`.
2. For each file, identify the primary audience and the primary question it answers.
3. Classify the file using the documentation-area rules above.
4. If a file mixes multiple concerns, split by dominant concern instead of forcing one large document into the wrong area.
5. Rewrite the content so it matches the target section:
   - development: concise operational guidance for contributors
   - architecture: structural explanations, boundaries, diagrams, deployment intent
   - external: dependency-centric reference guidance
   - user: user-centric behavior and workflows
6. Save the result under the chosen docs subtree using a stable, descriptive markdown filename.
7. Add or update nearby index or navigation files if that docs subtree already uses them.
8. Report the final placement decisions and any unresolved ambiguity.

## Decision Check

Use this quick discriminator before placing a document:

- If the main reader is a contributor working on the repo, prefer `development`.
- If the main reader needs to understand system shape or deployment design, prefer `architecture`.
- If the document mainly explains a dependency, platform, or external API, prefer `external`.
- If the main reader is operating or learning the product itself, prefer `user`.

If two areas seem plausible, choose the one that best matches the document's dominant purpose and move the remaining material into a separate follow-up document.

## Current `.raw/` Mapping For This Repository

Based on the current source files:

- `.raw/product-overview.md` -> `docs/user/` because it describes product purpose, capabilities, workflow phases, and target users.
- `.raw/application-tech-stack.md` -> `docs/external/` because it is primarily a dependency and technology reference for the stack used by the application.
- `.raw/deployment-structure.md` -> `docs/architecture/` because it describes runtime roles, deployment topology, shared volumes, and container responsibilities.

No current `.raw/` source clearly belongs in `docs/development/`.

## Quality Criteria

The integration is complete when:

- every `.raw/` source has an explicit destination decision
- the rewritten document matches the target audience
- content is not duplicated across documentation areas without reason
- filenames are descriptive and stable
- placement decisions and remaining gaps are summarized clearly
- if the document contains multiple concerns, it is split into separate documents that each fit a single area
- if the document contains guidelines, principles and best-practices, extract the key facts and common information and place it in the most relevant area, then link to it from the other areas as needed

## Output Expectations

When using this skill, produce:

1. a placement decision for each input file
2. the target path or proposed target path
3. any required content split or rewrite note
4. any follow-up task, such as navigation or cross-link updates

## AGENTS.md

If a general principle affects the classification or rewrite of documents, add it to `AGENTS.md` as a principle or best practice for future reference. For example, if you find that many documents contain mixed concerns, you might add a principle about splitting documents by dominant concern to ensure clearer classification in the future.
