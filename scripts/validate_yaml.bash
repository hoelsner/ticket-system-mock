#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
webapp_dir="$repo_root/src/webapp"
python_bin="$webapp_dir/.venv/bin/python3"

if [[ ! -x "$python_bin" ]]; then
	echo "python interpreter not found at $python_bin"
	exit 1
fi

if ! "$python_bin" -c "import yaml" >/dev/null 2>&1; then
	echo "PyYAML is not available in the webapp virtual environment"
	exit 1
fi

mapfile -d '' yaml_files < <(
	find "$repo_root" \
		-type f \
		\( -name '*.yaml' -o -name '*.yml' \) \
		-not -path "$webapp_dir/.venv/*" \
		-not -path "$repo_root/runtime/*" \
		-not -path "$webapp_dir/runtime/*" \
		-print0 | sort -z
)

if [[ ${#yaml_files[@]} -eq 0 ]]; then
	echo "no yaml files found"
	exit 0
fi

"$python_bin" - "${yaml_files[@]}" <<'PY'
import pathlib
import sys

import yaml

errors = []

for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)

    try:
        with path.open(encoding="utf-8") as handle:
            list(yaml.safe_load_all(handle))
    except yaml.YAMLError as exc:
        errors.append(f"{path}: {exc}")

if errors:
    print("invalid yaml files detected:")
    for error in errors:
        print(error)
    raise SystemExit(1)

print(f"validated {len(sys.argv) - 1} yaml file(s)")
PY