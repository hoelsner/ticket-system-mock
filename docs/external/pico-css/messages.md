# Pico CSS Messages

## Purpose

This guide describes the project pattern for rendering Django messages framework
feedback with Pico CSS-friendly markup.

## Role in This Project

The web application uses Django's built-in messages framework for transient UI
feedback such as:

- informational prompts after redirects to the sign-in page
- success confirmation after issue workflow actions
- error feedback after failed authentication or invalid form submissions

Pico CSS does not provide a dedicated alert component, so this project uses a
semantic `section` with `article` elements and a small set of custom modifier
classes.

## Template Pattern

Render the shared message panel once in the base template so all pages inherit
the same behavior.

```html
{% if messages %}
  <section class="message-panel" aria-label="System messages">
    {% for message in messages %}
      <article
        class="message-panel__item message-panel__item--{{ message.level_tag }}"
        {% if message.level_tag == "error" %}role="alert"{% else %}role="status"{% endif %}
      >
        <p class="message-panel__eyebrow">{{ message.level_tag|title }}</p>
        <p>{{ message }}</p>
      </article>
    {% endfor %}
  </section>
{% endif %}
```

## CSS Pattern

Use Pico CSS defaults for spacing and typography, then add minimal modifiers for
the message variants.

```css
.message-panel {
    display: grid;
    gap: 0.75rem;
}

.message-panel__item {
    padding: 0.9rem 1rem;
    border: 1px solid var(--pico-muted-border-color);
    border-left-width: 0.4rem;
    border-radius: 0.9rem;
    background: var(--pico-card-background-color);
}

.message-panel__item--info {
    border-left-color: #2563eb;
}

.message-panel__item--success {
    border-left-color: #15803d;
}

.message-panel__item--warning {
    border-left-color: #b45309;
}

.message-panel__item--error {
    border-left-color: #b91c1c;
}
```

## Django View Pattern

Prefer adding messages in shared view hooks and redirect handlers instead of
hand-writing page-specific status banners.

```python
from django.contrib import messages

messages.info(request, "Sign in to continue in the user frontend.")
messages.success(request, f"Issue {issue.issue_number} was updated.")
messages.error(request, "Review the highlighted fields and try again.")
```

## Project Guidance

- Keep the message renderer in the base template instead of duplicating it per
  page.
- Use Django message levels (`info`, `success`, `warning`, `error`) as the
  canonical mapping for panel variants.
- Keep field-level validation errors near the form fields and use the message
  panel for page-level feedback.
- Use `role="alert"` for error messages and `role="status"` for non-error
  messages.