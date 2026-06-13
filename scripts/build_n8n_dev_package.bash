#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
package_root="${repo_root}/src/n8n_node"
stage_root="${repo_root}/.devcontainer/development/n8n/custom/node_modules/n8n-nodes-ticket-system-mock"

rm -rf "${stage_root}"
mkdir -p "${stage_root}"

pushd "${repo_root}" >/dev/null
make n8n-node-build
popd >/dev/null

cp "${package_root}/package.json" "${stage_root}/package.json"
cp -R "${package_root}/dist" "${stage_root}/dist"

echo "Staged local n8n dev package at ${stage_root}"