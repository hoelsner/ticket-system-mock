# External Documentation Index

## Purpose

This area documents external frameworks, libraries, and technology choices that
the application depends on or integrates with.

## Documents

| Document | Primary Purpose |
| --- | --- |
| [Application Technology Reference](application-stack/technology-reference.md) | Summarizes the primary external technologies used by the application and the role each one plays in the system. |
| [Django Internationalization and Localization](django/internationalization.md) | Explains the Django-native approach for multilingual application support, including settings, middleware, translation tags, and message catalog workflow. |
| [Django Admin Basic Usage](django-admin/basic-usage.md) | Explains how Django Admin is used as the internal administration frontend in this project. |
| [Django Cotton Basic Usage](django-cotton/basic-usage.md) | Explains how Django Cotton is used to build reusable components in the user frontend. |
| [Django Ninja Basic Usage](django-ninja/basic-usage.md) | Explains how Django Ninja is used to provide the REST API surface for integrations and automation. |
| [HTMX with HTTP Server-Sent Events](htmx/server-sent-events.md) | Explains the project pattern for live UI updates with HTMX and server-sent events. |
| [Iconify Basic Usage](iconify/basic-usage.md) | Explains how Iconify icon sets are browsed and how a small MIT-licensed subset can be vendored into the application as local inline SVG icons. |
| [n8n Custom Node Development](n8n/README.md) | Explains how to plan, implement, validate, and distribute custom n8n nodes for this repository. |
| [n8n Planning and Architecture](n8n/planning-and-architecture.md) | Explains how to choose the right node type, implementation style, UI design, and architecture boundary for the project's n8n integration. |
| [n8n Implementation Reference](n8n/implementation-reference.md) | Explains the practical node-building details for metadata, credentials, UI elements, errors, versioning, and item linking. |
| [n8n Testing and Distribution](n8n/testing-and-distribution.md) | Explains local validation, troubleshooting, private installation, and optional community distribution requirements for the project's n8n node. |
| [Pico CSS Basic Usage](pico-css/basic-usage.md) | Explains how Pico CSS is used as the baseline styling layer for the user frontend. |
| [Pico CSS Cards](pico-css/cards.md) | Explains the semantic Pico CSS card pattern and how to apply it to issue and dashboard style UI blocks. |
| [Pico CSS Grid](pico-css/grid.md) | Explains Pico CSS `.grid` usage for lightweight responsive layouts and when to switch to native CSS Grid rules. |
| [Pico CSS Messages](pico-css/messages.md) | Explains the project pattern for Django messages framework feedback panels built on top of Pico CSS articles and light custom modifiers. |
| [Pico CSS Tooltip](pico-css/tooltip.md) | Explains the project pattern for Pico CSS tooltips using `data-tooltip` and optional placement attributes. |