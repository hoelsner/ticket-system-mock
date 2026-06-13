#!/bin/bash
#
# This script compiles the Ticket System Mock Python SDK sources.
# It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

cd "$sdk_dir" || exit 1

printf "compiling Ticket System Mock SDK python sources... "
run_silent prepare_environment
run_silent env PYTHONPATH="$sdk_dir" "$python_bin" -m compileall -q ticketsystemmock tests