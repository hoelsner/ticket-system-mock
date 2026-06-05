# Iconify Basic Usage

## Purpose

This guide explains how to use Iconify as the source catalog for icons in the
web application.

## What the Site Provides

The Iconify icon sets site at
[icon-sets.iconify.design](https://icon-sets.iconify.design/) is a searchable
catalog of open source icon sets.

It organizes icon sets by:

- category, such as UI, programming, logos, emoji, or flags
- icon grid style, such as 24px or mixed grid sets
- palette and license metadata

Each icon page exposes:

- the icon name in `prefix:name` format
- the author and license
- an SVG code snippet
- links back to the source icon set

## Project Pattern

This project does not load Iconify from a CDN and does not add a frontend icon
runtime dependency just to render a few navigation icons.

Instead, the project uses Iconify as the discovery source and then vendors a
small, fixed set of inline SVG icons directly in Django templates.

The current application pattern is:

1. Browse Iconify and pick a license-compatible icon set.
2. Prefer permissive licenses such as MIT, Apache 2.0, or CC0.
3. Copy the SVG path data for only the icons the application actually uses.
4. Render those icons through one shared Django template include.
5. Style icons with local CSS so the application stays self-contained.

## Current Application Choice

The user frontend currently uses a small subset of
[Tabler Icons](https://icon-sets.iconify.design/tabler/) through Iconify.

Reasons for this choice:

- the set is MIT-licensed
- the icons are visually consistent for navigation and workflow actions
- the SVG output is compact and easy to vendor locally

## Example Usage Pattern

The application uses one shared template include for icons and passes a small
symbolic name into that include.

```html
<a href="{% url 'dashboard' %}" class="app-inline-icon-link">
  {% include "includes/icon.html" with name="dashboard" %}
  <span>Dashboard</span>
</a>
```

This keeps icon usage:

- local to the application
- easy to audit
- independent of third-party runtime availability

## Guidance

- Use Iconify for icon discovery and license review.
- Keep the in-application icon set intentionally small.
- Prefer one visual family per UI surface instead of mixing unrelated icon
  styles.
- Keep icons decorative when adjacent text already communicates the action.
- Add a new vendored icon only when it improves a real navigation or workflow
  action.