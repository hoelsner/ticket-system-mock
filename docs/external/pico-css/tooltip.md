# Pico CSS Tooltip

## Purpose

This guide defines the project pattern for tooltips built with Pico CSS.

## Project Pattern

Pico CSS exposes tooltips through the `data-tooltip` attribute. This project
uses that attribute instead of the native `title` tooltip when an element needs
visible hover or focus help text.

```html
<button data-tooltip="Archive issue">Archive</button>
```

## Placement

Pico CSS shows the tooltip above the element by default. Change the position
with `data-placement` when the default would clip or cover nearby UI.

```html
<button data-tooltip="Open issue details">Open</button>
<button data-tooltip="Close dialog" data-placement="left">Close</button>
```

Supported placements:

- `top`
- `right`
- `bottom`
- `left`

## Accessibility Guidance

- Keep `aria-label` on icon-only controls so screen readers still announce the
  control clearly.
- Use `data-tooltip` for the visible tooltip text.
- Prefer short action phrases such as `Edit issue` or `Archive issue`.

## Project Guidance

- Use Pico CSS tooltips for icon-only actions in the user frontend.
- Do not mix `title` and `data-tooltip` on the same control.
- Add `data-placement` only when the default top placement is not suitable.