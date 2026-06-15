#!/bin/bash
#
# This script runs mypy checks for the web application. It should be run from the root of the repository.
#
set -o pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
webapp_dir="$repo_root/src/webapp"
python_bin="$webapp_dir/.venv/bin/python3"

cd "$webapp_dir" || exit 1

if [[ ! -x "$python_bin" ]]; then
    echo "python interpreter not found at $python_bin"
    exit 1
fi

if ! "$python_bin" -m mypy --help >/dev/null 2>&1; then
    echo "mypy is not available in the webapp virtual environment"
    exit 1
fi

run_silent() {
    local tmpfile
    tmpfile=$(mktemp)
    "$@" > "$tmpfile" 2>&1
    local status=$?
    if [[ $status -ne 0 ]]; then
        cat "$tmpfile"
        rm -f "$tmpfile"
        exit $status
    fi
    rm -f "$tmpfile"
    echo "OK"
}

printf "type checking webapp python sources... "
run_silent env DJANGO_SETTINGS_MODULE=djangoapp.settings "$python_bin" -m mypy djangoapp manage.py