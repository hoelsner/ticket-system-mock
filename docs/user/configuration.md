# Configuration Guide

## Purpose

This guide describes the environment variables used by the Web Application and
the default value applied when a variable is not provided.

## Configuration Table

| Environment Variable | Default Value | Used For |
| --- | --- | --- |
| `DJANGO_DEBUG` | `True` | Enables or disables Django debug mode. Accepted true values are `1`, `true`, `yes`, and `on` in any letter case. |
| `DJANGO_SECRET_KEY` | `django-insecure-^d!g3oga6mmxg&&6)if8+2s-^6u7_etn-(3&3g4h3-z+yo*iwu` | Sets Django's secret key. |
| `SERVICE_BASE_URL` | `http://localhost` | Defines the canonical externally exposed base URL that API consumers can prepend to relative REST API URLs such as attachment download paths. |
| `DJANGO_ALLOWED_HOSTS` | `*` | Sets the allowed hosts list as a comma-separated value. |
| `DJANGO_TIME_ZONE` | `UTC` | Sets the Django application time zone. |
| `DJANGO_LOG_LEVEL` | `DEBUG` when `DJANGO_DEBUG=True`, otherwise `INFO` | Sets the Django logging level used by the basic stdout logging configuration. |
| `PRODUCT_DISPLAY_NAME` | `IT Operation Ticketing Demo Service` | Provides the default product name used by the frontend, admin, and branding fallback behavior. |
| `DJANGO_STATIC_ROOT` | `src/webapp/runtime/static` | Sets the filesystem path where Django writes collected static files. |
| `DJANGO_MEDIA_ROOT` | `src/webapp/runtime/media` | Sets the filesystem path where Django stores media files. |
| `POSTGRES_DB` | `itoticketing` | Sets the PostgreSQL database name used by the Web Application. |
| `POSTGRES_USER` | `itoticketing` | Sets the PostgreSQL user name used by the Web Application. |
| `POSTGRES_PASSWORD` | `PlsChgMePostgres` | Sets the PostgreSQL password used by the Web Application. |
| `POSTGRES_HOST` | `database` | Sets the PostgreSQL host used by the Web Application. |
| `POSTGRES_PORT` | `5432` | Sets the PostgreSQL port used by the Web Application. |
| `CACHE_PASSWORD` | `PlsChgMeCache` | Sets the Redis password used by the Web Application cache configuration. |
| `CACHE_HOST` | `cache` | Sets the Redis host used by the Web Application cache configuration. |
| `CACHE_PORT` | `6379` | Sets the Redis port used by the Web Application cache configuration. |
| `CACHE_DB` | `0` | Sets the Redis database index used by the Web Application cache configuration. |

Each configuration item that is currently read from the environment is listed
in the table above.

REST API URL fields remain relative by design. Attachment payloads expose
`file_url` as a relative download path. Integration systems should prepend
`SERVICE_BASE_URL` when they need to construct a full external URL.

When `DJANGO_DEBUG` is enabled, Django password validators are disabled to keep
local development simpler. In non-debug mode, the standard Django password
validators are enabled.

The application also defines a basic Django logging configuration that writes to
standard output. The log level is `DEBUG` when `DJANGO_DEBUG=True` and `INFO`
otherwise.

## Branding Administration

Runtime branding is split between environment configuration and admin-managed
media assets.

- `PRODUCT_DISPLAY_NAME` provides the fallback product name for the application.
- Django Admin exposes one `App Branding` record that can override the display
	name, upload a custom navbar logo and login background image, and set the
	primary Pico CSS accent colors used by the user frontend in light mode and
	dark mode.
- If no branding record exists, the application falls back to the default
	product name, bundled placeholder images, and the default Pico CSS primary
	palette.
- Uploaded branding assets are stored under `DJANGO_MEDIA_ROOT`, so deployments
	should treat media storage as persistent runtime content.

## Example

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=django-insecure-^d!g3oga6mmxg&&6)if8+2s-^6u7_etn-(3&3g4h3-z+yo*iwu
SERVICE_BASE_URL=http://localhost
DJANGO_ALLOWED_HOSTS=*
DJANGO_TIME_ZONE=UTC
DJANGO_LOG_LEVEL=DEBUG
PRODUCT_DISPLAY_NAME=IT Operation Ticketing Demo Service
DJANGO_STATIC_ROOT=/app/runtime/static
DJANGO_MEDIA_ROOT=/app/runtime/media
POSTGRES_DB=itoticketing
POSTGRES_USER=itoticketing
POSTGRES_PASSWORD=PlsChgMePostgres
POSTGRES_HOST=database
POSTGRES_PORT=5432
CACHE_PASSWORD=PlsChgMeCache
CACHE_HOST=cache
CACHE_PORT=6379
CACHE_DB=0
```