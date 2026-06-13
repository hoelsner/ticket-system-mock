#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
n8n_node_dir="$repo_root/src/n8n_node"

cd "$n8n_node_dir"

npm run pack:node >/dev/null 2>&1

package_name="$(node -p "require('./package.json').name")"
package_version="$(node -p "require('./package.json').version")"
package_archive="build/${package_name}-${package_version}.tgz"

if [[ ! -f "$package_archive" ]]; then
    echo "expected package archive was not created: $package_archive" >&2
    exit 1
fi

mapfile -t archive_entries < <(tar -tzf "$package_archive")

if [[ ${#archive_entries[@]} -eq 0 ]]; then
    echo "package archive is empty: $package_archive" >&2
    exit 1
fi

declare -A archive_entry_map=()

for archive_entry in "${archive_entries[@]}"; do
    archive_entry_map["$archive_entry"]=1
done

mapfile -t expected_entries < <(
    node <<'EOF'
const packageJson = require('./package.json');
const expectedEntries = [
  'package/package.json',
  'package/dist/index.js',
  ...packageJson.n8n.credentials.map((entry) => `package/${entry}`),
  ...packageJson.n8n.nodes.map((entry) => `package/${entry}`),
];

for (const entry of expectedEntries) {
  console.log(entry);
}
EOF
)

for expected_entry in "${expected_entries[@]}"; do
    if [[ -z "${archive_entry_map[$expected_entry]:-}" ]]; then
        echo "package archive is missing expected entry: $expected_entry" >&2
        exit 1
    fi
done

echo "validated n8n package archive: $package_archive"