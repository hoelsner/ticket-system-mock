# Pico CSS Basic Usage

## Purpose

This guide summarizes the basic project usage of Pico CSS for the user
frontend.

## Role in This Project

Pico CSS provides the baseline styling for the user frontend. It works best
with semantic HTML and light custom styling on top.

## Local Stylesheet Usage

Load the vendored stylesheet from the Django static files system.

```html
{% load static %}
<link rel="stylesheet" href="{% static 'lib/pico/pico.min.css' %}">
```

## Basic Page Structure

Pico CSS works well with semantic elements and a small amount of structure.

```html
<main class="container">
    <h1>Tickets</h1>
    <section>
        <p>Open work for the support team.</p>
    </section>
</main>
```

## Forms

Use standard HTML form elements before adding custom classes.

```html
<form>
    <label>
        Title
        <input type="text" name="title">
    </label>

    <label>
        Priority
        <select name="priority">
            <option>LOW</option>
            <option>MEDIUM</option>
            <option>HIGH</option>
        </select>
    </label>

    <button type="submit">Create Ticket</button>
</form>
```

## Project Guidance

- Use Pico CSS only for the user frontend.
- Prefer semantic HTML and small extensions over heavy custom utility layers.
- Combine Pico CSS with Cotton components so styling stays consistent across
  reusable UI elements.
- Keep the admin frontend on Django Admin styling rather than trying to make it
  match the user frontend.