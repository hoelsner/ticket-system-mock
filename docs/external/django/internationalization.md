# Django Internationalization and Localization

## Purpose

This guide summarizes the Django-native way to build a multilingual application
with built-in internationalization and localization support.

## Role in This Project

The application must support multiple languages across the user frontend, admin
frontend, and REST-adjacent user-facing text. Prefer Django's built-in i18n
system instead of a custom translation layer.

## Basic Configuration

Enable internationalization in Django settings and configure the middleware in
the recommended order.

```python
from django.utils.translation import gettext_lazy as _

USE_I18N = True

LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
]
```

According to the Django documentation, `LocaleMiddleware` should run after
`SessionMiddleware` and before `CommonMiddleware`.

## Mark Strings for Translation

Mark Python strings with Django's translation helpers.

```python
from django.utils.translation import gettext_lazy as _


class ExampleForm(forms.Form):
    title = forms.CharField(label=_("Title"))
```

Use `gettext_lazy` for module-level declarations such as model field labels,
form labels, and settings-driven display strings.

In templates, load the `i18n` tags and mark visible strings explicitly.

```django
{% load i18n %}

<h1>{% translate "Welcome" %}</h1>
<p>{% blocktranslate %}Open work for the support team.{% endblocktranslate %}</p>
```

## Language Switching

Expose Django's built-in language switching URLs.

```python
from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]
```

This allows the application to use Django's standard `set_language` flow for
switching the active language.

## Translation Files

Store project translation files in locale directories and generate message
catalogs with Django's management commands.

```bash
django-admin makemessages -a
django-admin compilemessages
```

`makemessages` extracts marked strings from Python modules and templates.
`compilemessages` builds the binary message catalogs used at runtime.

## Project Guidance

- Use Django's built-in i18n system for multilingual support.
- Keep supported languages explicit in `LANGUAGES`.
- Add `LocaleMiddleware` instead of implementing custom language resolution.
- Mark all user-visible strings in Python and templates for translation.
- Keep project translation files in a shared `locale/` directory referenced by
  `LOCALE_PATHS` unless app-local locale directories are intentionally needed.
- Treat language switching as part of normal UI behavior for both the user and
  admin frontends.