#!/bin/bash
#
# This script runs Bandit checks for the web application. It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
webapp_dir="$repo_root/src/webapp"
python_bin="$webapp_dir/.venv/bin/python3"
report_dir="$webapp_dir/covreport"
bandit_targets=("djangoapp" "manage.py")

cd "$webapp_dir" || exit 1

if [[ ! -x "$python_bin" ]]; then
    echo "python interpreter not found at $python_bin"
    exit 1
fi

if ! "$python_bin" -m bandit --version >/dev/null 2>&1; then
    echo "bandit is not available in the webapp virtual environment"
    exit 1
fi

run_silent() {
    local tmpfile
    tmpfile=$(mktemp)
    "$@" > "$tmpfile" 2>&1
    local status=$?
    if [[ $status -ne 0 ]]; then
        cat "$tmpfile"
        rm -f "$tmpfile"
        exit $status
    fi
    rm -f "$tmpfile"
    echo "OK"
}

run_bandit() {
    mkdir -p "$report_dir"

    "$python_bin" -m bandit -r "${bandit_targets[@]}" -ll \
        --exclude tests,*/tests/*,*/test_*.py \
        --format html --output "$report_dir/bandit_report.html"
}

printf "running bandit tests... "
run_silent run_bandit