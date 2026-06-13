#!/bin/bash
#
# This script runs the unit tests for the Ticket System Mock Python SDK.
# It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

printf "running Ticket System Mock SDK unit tests... "
run_silent prepare_environment
run_silent env PYTHONPATH="$sdk_dir" "$python_bin" -m unittest "$sdk_dir/tests/tests_sdk.py"