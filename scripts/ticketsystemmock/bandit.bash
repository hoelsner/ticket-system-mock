#!/bin/bash
#
# This script runs Bandit checks for the Ticket System Mock Python SDK.
# It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

bandit_targets=("ticketsystemmock")

cd "$sdk_dir" || exit 1

run_bandit() {
    mkdir -p "$report_dir"

    env PYTHONPATH="$sdk_dir" "$python_bin" -m bandit -r "${bandit_targets[@]}" -ll \
        --exclude tests,*/tests/*,*/test_*.py,*/.venv/* \
        --format html --output "$report_dir/bandit_report.html"
}

printf "running Ticket System Mock SDK bandit tests... "
run_silent prepare_dev_environment
run_silent run_bandit