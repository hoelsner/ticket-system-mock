#!/bin/bash
#
# This script cleans up the directories by removing Python bytecode files and __pycache__ directories. 
# It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
webapp_dir="$repo_root/src/webapp"

cd "$webapp_dir" || exit 1

find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete