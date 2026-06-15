#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
n8n_node_dir="$repo_root/src/n8n_node"
report_dir="$n8n_node_dir/covreport"
node_modules_bin="$n8n_node_dir/node_modules/.bin"

ensure_package_dir() {
    if [[ ! -d "$n8n_node_dir" ]]; then
        echo "n8n node package directory not found at $n8n_node_dir"
        exit 1
    fi
}

ensure_package_dependencies() {
    if [[ -x "$node_modules_bin/tsc" && -x "$node_modules_bin/eslint" && -x "$node_modules_bin/c8" ]]; then
        return 0
    fi

    cd "$n8n_node_dir" || exit 1
    npm ci
}

prepare_environment() {
    ensure_package_dir
    ensure_package_dependencies
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