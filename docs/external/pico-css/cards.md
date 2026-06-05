# Pico CSS Cards

## Purpose

This guide explains how to create cards with Pico CSS in this project.

## Basic Pattern

Pico CSS uses semantic HTML for cards. The base pattern is a plain
`<article>` element.

```html
<article>
    I am a card.
</article>
```

Pico CSS applies spacing and card styling without requiring extra utility
classes.

## Sectioning

Use `<header>` and `<footer>` inside the `<article>` when the card needs a
title area or actions.

```html
<article>
    <header>
        <strong>Issue #1234</strong>
    </header>

    Network connectivity is unstable for the branch office.

    <footer>
        <small>Updated 5 minutes ago</small>
    </footer>
</article>
```

This is the main Pico CSS card structure documented by Pico itself.

## Project Example

For this project, cards fit well for issue summaries, dashboard tiles, or
small status blocks in the user frontend.

```html
<article>
    <header>
        <strong>Issue INC-2026-0042</strong>
    </header>

    <p><strong>Category:</strong> Incident</p>
    <p><strong>Workflow State:</strong> IN_PROGRESS</p>
    <p><strong>Priority:</strong> HIGH</p>

    <footer>
        <a href="#">Open issue</a>
    </footer>
</article>
```

## Guidance

- Prefer semantic HTML over custom wrapper classes when building cards.
- Use `<header>` for a compact summary or label block.
- Use `<footer>` for links, secondary actions, or metadata.
- Keep card bodies short and scannable.
- If a card becomes structurally complex, move repeated markup into a Cotton
  component instead of duplicating template fragments.

## Related Guidance

- See [basic-usage.md](basic-usage.md) for the baseline Pico CSS setup in this
  repository.
- See the Pico CSS card documentation at
  <https://picocss.com/docs/card> for the upstream reference.