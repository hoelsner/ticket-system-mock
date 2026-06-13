#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
SDK_DIR="$REPO_ROOT/src/ticketsystemmock"
TEMP_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$TEMP_DIR"
}

trap cleanup EXIT

uv build --sdist "$SDK_DIR" -o "$TEMP_DIR" --clear --no-build-logs >/dev/null 2>&1

package_name=$(python3 - <<'PY' "$SDK_DIR/pyproject.toml"
import pathlib
import sys
import tomllib

pyproject = tomllib.loads(pathlib.Path(sys.argv[1]).read_text())
name = pyproject["project"]["name"]
version = pyproject["project"]["version"]
print(f"{name}-{version}.tar.gz")
PY
)

package_archive="$TEMP_DIR/$package_name"

if [[ ! -f "$package_archive" ]]; then
    echo "expected SDK source distribution was not created: $package_archive" >&2
    exit 1
fi

mapfile -t archive_entries < <(tar -tzf "$package_archive")

if [[ ${#archive_entries[@]} -eq 0 ]]; then
    echo "SDK source distribution is empty: $package_archive" >&2
    exit 1
fi

declare -A archive_entry_map=()

for archive_entry in "${archive_entries[@]}"; do
    archive_entry_map["$archive_entry"]=1
done

package_root="${package_name%.tar.gz}"
expected_entries=(
    "$package_root/pyproject.toml"
    "$package_root/README.md"
    "$package_root/ticketsystemmock/__init__.py"
    "$package_root/ticketsystemmock/client.py"
    "$package_root/ticketsystemmock/transport.py"
)

for expected_entry in "${expected_entries[@]}"; do
    if [[ -z "${archive_entry_map[$expected_entry]:-}" ]]; then
        echo "SDK source distribution is missing expected entry: $expected_entry" >&2
        exit 1
    fi
done

echo "validated Python SDK source distribution: $package_archive"