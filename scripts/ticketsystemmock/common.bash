#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
sdk_dir="$repo_root/src/ticketsystemmock"
venv_dir="$sdk_dir/.venv"
python_bin="$venv_dir/bin/python3"
report_dir="$sdk_dir/covreport"

ensure_sdk_dir() {
    if [[ ! -d "$sdk_dir" ]]; then
        echo "SDK directory not found at $sdk_dir"
        exit 1
    fi
}

ensure_virtualenv() {
    if [[ -x "$python_bin" ]]; then
        return 0
    fi

    uv venv --python 3.14 "$venv_dir"
}

ensure_package_dependencies() {
    if env PYTHONPATH="$sdk_dir" "$python_bin" -c "import httpx, ticketsystemmock" >/dev/null 2>&1; then
        return 0
    fi

    "$python_bin" -m pip install -q -e "$sdk_dir"
}

ensure_dev_tools() {
    if "$python_bin" -c "import bandit, coverage, mypy, radon" >/dev/null 2>&1; then
        return 0
    fi

    "$python_bin" -m pip install -q bandit coverage mypy radon
}

prepare_environment() {
    ensure_sdk_dir
    ensure_virtualenv
    ensure_package_dependencies
}

prepare_dev_environment() {
    prepare_environment
    ensure_dev_tools
}

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