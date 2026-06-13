# Development Documentation Index

## Purpose

This area documents contributor-facing rules, shared design decisions, and
implementation guidance used during development.

## Documents

| Document | Primary Purpose |
| --- | --- |
| [Instance Kanban Board Drag And Drop And State Sync](instance-kanban-drag-and-drop-and-state-sync.md) | Defines the contributor-facing implementation plan for drag-and-drop Issue movement, backend reconciliation, and edit-lock indicators on the Instance Kanban Board. |
| [Coding and Documentation Standards](coding-and-documentation-standards.md) | Defines the baseline standards contributors should follow when writing code and maintaining project documentation. |
| [Data Model](data-model.md) | Defines the conceptual domain model, core entities, relationships, and modeling decisions before database implementation details are finalized. |
| [Issue Lifecycle And Attachments](issue-lifecycle-and-attachments.md) | Describes contributor-facing lifecycle, attachment, mention, and audit rules that support the issue workflow. |
| [Local Build And Production Test Verification](local-build-and-production-test-verification.md) | Documents the end-to-end commands for building the production image locally, generating a deployment bundle, starting a production-style local stack, and verifying the result. |
| [n8n Local Smoke Test](n8n-local-smoke-test.md) | Documents the manual Docker-based n8n runtime used for contributor smoke tests against the local webapp API. |
| [n8n Node Use And Build](n8n-node-use-and-build.md) | Summarizes the role of the n8n package, the local build and pack commands, and how the packaged artifact is bundled into the webapp image. |
| [Webhook Delivery](webhook-delivery.md) | Describes how webhook events are persisted, delivered after transaction commit, retried, and recovered after worker interruption. |
| [Webapp Sitemap](webapp-sitemap.md) | Summarizes the current Django route structure for the user frontend, authentication views, admin surface, and REST API. |