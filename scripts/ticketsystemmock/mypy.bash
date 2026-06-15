#!/bin/bash
#
# This script runs mypy checks for the Ticket System Mock Python SDK.
# It should be run from the root of the repository.
#
set -o pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

cd "$sdk_dir" || exit 1

printf "type checking Ticket System Mock SDK python sources... "
run_silent prepare_dev_environment
run_silent env PYTHONPATH="$sdk_dir" "$python_bin" -m mypy ticketsystemmock tests