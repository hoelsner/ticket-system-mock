#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
N8N_NODE_DIR="$REPO_ROOT/src/n8n_node"
SOURCE_BUILD_DIR="$N8N_NODE_DIR/build"
DEVSERVER_INTEGRATIONS_DIR="$REPO_ROOT/build/integrations"
PACKAGE_GLOB='n8n-nodes-ticket-system-mock-*.tgz'

cd "$N8N_NODE_DIR"
npm run pack:node

mkdir -p "$DEVSERVER_INTEGRATIONS_DIR"
find "$DEVSERVER_INTEGRATIONS_DIR" -maxdepth 1 -type f -name "$PACKAGE_GLOB" -delete

shopt -s nullglob
package_files=("$SOURCE_BUILD_DIR"/$PACKAGE_GLOB)
shopt -u nullglob

if [[ ${#package_files[@]} -eq 0 ]]; then
    echo "No n8n package archive was produced in $SOURCE_BUILD_DIR" >&2
    exit 1
fi

mv "${package_files[@]}" "$DEVSERVER_INTEGRATIONS_DIR/"

echo "Staged n8n package in $DEVSERVER_INTEGRATIONS_DIR"
ls -1 "$DEVSERVER_INTEGRATIONS_DIR"/$PACKAGE_GLOB