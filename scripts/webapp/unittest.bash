#!/bin/bash
#
# This script runs the unit tests for the web application. It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
webapp_dir="$repo_root/src/webapp"
python_bin="$webapp_dir/.venv/bin/python3"

cd "$webapp_dir" || exit 1

if [[ ! -x "$python_bin" ]]; then
    echo "python interpreter not found at $python_bin"
    exit 1
fi

# Runs a command silently; only prints output if the command fails.
run_silent() {
    local tmpfile
    tmpfile=$(mktemp)
    "$@" > "$tmpfile" 2>&1
    local status=$?
    if [ $status -ne 0 ]; then
        cat "$tmpfile"
        rm -f "$tmpfile"
        exit $status
    fi
    rm -f "$tmpfile"
    echo "OK"
}

printf "running unit tests... "
run_silent env "$python_bin" manage.py test --noinput
