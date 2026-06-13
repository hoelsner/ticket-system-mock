#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
SDK_DIR="$REPO_ROOT/src/ticketsystemmock"
DEVSERVER_INTEGRATIONS_DIR="$REPO_ROOT/build/integrations"
PACKAGE_GLOB='ticketsystemmock-*.tar.gz'
TEMP_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$TEMP_DIR"
}

trap cleanup EXIT

mkdir -p "$DEVSERVER_INTEGRATIONS_DIR"
find "$DEVSERVER_INTEGRATIONS_DIR" -maxdepth 1 -type f -name "$PACKAGE_GLOB" -delete

uv build --sdist "$SDK_DIR" -o "$TEMP_DIR" --clear --no-build-logs

shopt -s nullglob
package_files=("$TEMP_DIR"/$PACKAGE_GLOB)
shopt -u nullglob

if [[ ${#package_files[@]} -eq 0 ]]; then
    echo "No Python SDK source distribution was produced in $TEMP_DIR" >&2
    exit 1
fi

mv "${package_files[@]}" "$DEVSERVER_INTEGRATIONS_DIR/"

echo "Staged Python SDK package in $DEVSERVER_INTEGRATIONS_DIR"
ls -1 "$DEVSERVER_INTEGRATIONS_DIR"/$PACKAGE_GLOB