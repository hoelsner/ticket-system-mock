#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

webapp_dir="${WEBAPP_DIR:-$repo_root/src/webapp}"
runtime_root="${DJANGO_RUNTIME_ROOT:-$repo_root/runtime}"
static_root="${DJANGO_STATIC_ROOT:-$runtime_root/static}"
media_root="${DJANGO_MEDIA_ROOT:-$runtime_root/media}"
python_bin="${PYTHON_BIN:-$webapp_dir/.venv/bin/python3}"
gunicorn_bin="${GUNICORN_BIN:-$webapp_dir/.venv/bin/gunicorn}"
bind_host="${GUNICORN_BIND_HOST:-0.0.0.0}"
bind_port="${GUNICORN_BIND_PORT:-8000}"
worker_count="${GUNICORN_WORKERS:-2}"
thread_count="${GUNICORN_THREADS:-2}"
timeout_seconds="${GUNICORN_TIMEOUT:-60}"
graceful_timeout_seconds="${GUNICORN_GRACEFUL_TIMEOUT:-30}"
keepalive_seconds="${GUNICORN_KEEPALIVE:-5}"
log_level="${GUNICORN_LOG_LEVEL:-info}"
app_module="${GUNICORN_APP_MODULE:-djangoapp.wsgi:application}"

if [[ ! -x "$python_bin" ]]; then
	python_bin="${PYTHON_BIN_FALLBACK:-python3}"
fi

if [[ ! -d "$webapp_dir" ]]; then
	echo "webapp directory not found at $webapp_dir"
	exit 1
fi

cd "$webapp_dir" || exit 1

mkdir -p "$static_root" "$media_root"

export DJANGO_STATIC_ROOT="$static_root"
export DJANGO_MEDIA_ROOT="$media_root"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-djangoapp.settings}"

if [[ -x "$gunicorn_bin" ]]; then
	gunicorn_cmd=("$gunicorn_bin")
elif "$python_bin" -m gunicorn --version >/dev/null 2>&1; then
	gunicorn_cmd=("$python_bin" -m gunicorn)
else
	echo "gunicorn is not available. Install it in the webapp environment or set GUNICORN_BIN."
	exit 1
fi

echo "starting gunicorn for $app_module on $bind_host:$bind_port"

exec "${gunicorn_cmd[@]}" \
	--bind "$bind_host:$bind_port" \
	--workers "$worker_count" \
	--threads "$thread_count" \
	--timeout "$timeout_seconds" \
	--graceful-timeout "$graceful_timeout_seconds" \
	--keep-alive "$keepalive_seconds" \
	--access-logfile - \
	--error-logfile - \
	--log-level "$log_level" \
	$app_module