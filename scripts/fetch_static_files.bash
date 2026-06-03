#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
target_root="$repo_root/src/webapp/static/lib"

htmx_version="2.0.10"
htmx_sse_version="2.2.4"
pico_version="2.1.1"

mkdir -p \
    "$target_root/htmx" \
    "$target_root/htmx-ext-sse" \
    "$target_root/pico"

download() {
    local url="$1"
    local output="$2"
    curl -fsSL "$url" -o "$output"
}

echo "downloading htmx $htmx_version"
download \
    "https://cdn.jsdelivr.net/npm/htmx.org@${htmx_version}/dist/htmx.min.js" \
    "$target_root/htmx/htmx.min.js"

echo "downloading htmx SSE extension $htmx_sse_version"
download \
    "https://cdn.jsdelivr.net/npm/htmx-ext-sse@${htmx_sse_version}/sse.js" \
    "$target_root/htmx-ext-sse/sse.js"

echo "downloading Pico CSS $pico_version"
download \
    "https://cdn.jsdelivr.net/npm/@picocss/pico@${pico_version}/css/pico.min.css" \
    "$target_root/pico/pico.min.css"

echo "static frontend libraries downloaded to $target_root"