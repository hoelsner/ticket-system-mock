# Pico CSS Grid

## Purpose

This guide explains how to use the Pico CSS grid helper in this project.

## Basic Pattern

Pico CSS provides a minimal grid helper through the `.grid` class. Apply it to
 a container and place columns inside it.

```html
<div class="grid">
    <div>1</div>
    <div>2</div>
    <div>3</div>
    <div>4</div>
</div>
```

Pico CSS uses this pattern for lightweight responsive layouts. Columns collapse
 on smaller devices, which keeps the layout readable without additional utility
 classes.

## Project Example

In this project, the grid helper is a good fit for dashboard summaries,
 side-by-side cards, or compact overview panels in the user frontend.

```html
<section class="grid">
    <article>
        <header>
            <strong>Assigned Issues</strong>
        </header>
        <p>12 active items</p>
    </article>

    <article>
        <header>
            <strong>Mentions</strong>
        </header>
        <p>3 comments need attention</p>
    </article>

    <article>
        <header>
            <strong>Escalations</strong>
        </header>
        <p>1 issue marked as escalated</p>
    </article>
</section>
```

## Guidance

- Use `.grid` for simple responsive layouts, not for a full design system.
- Prefer semantic child elements such as `<section>`, `<article>`, or other
  meaningful containers inside the grid.
- Combine `.grid` with Pico cards when you need evenly spaced dashboard or
  summary layouts.
- Do not force complex breakpoint-heavy behavior into Pico's grid helper. If a
  layout becomes highly customized, use native CSS Grid rules in project CSS.
- `.grid` is part of Pico's class-based usage and is not available in the
  class-less version.

## When to Use Native CSS Grid Instead

Use custom CSS Grid rules instead of `.grid` when you need:

- explicit column sizing
- named grid areas
- complex nested layouts
- different layout behavior across several breakpoints

Pico's own guidance keeps `.grid` intentionally minimal.

## Related Guidance

- See [basic-usage.md](basic-usage.md) for the baseline Pico CSS setup in this
  repository.
- See [cards.md](cards.md) for a matching Pico CSS card pattern that works well
  inside grid layouts.
- See the Pico CSS grid documentation at
  <https://picocss.com/docs/grid> for the upstream reference.