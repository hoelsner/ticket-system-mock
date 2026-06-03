#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

mapfile -d '' bash_files < <(find "$repo_root" -type f -name '*.bash' -print0 | sort -z)

if [[ ${#bash_files[@]} -eq 0 ]]; then
    echo "no bash scripts found"
    exit 0
fi

for bash_file in "${bash_files[@]}"; do
    bash -n "$bash_file"
done

echo "validated ${#bash_files[@]} bash script(s)"