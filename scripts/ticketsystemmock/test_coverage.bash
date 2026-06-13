#!/bin/bash
#
# This script runs the Ticket System Mock Python SDK unit tests with coverage.
# It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

coverage_threshold=98
coverage_config="$sdk_dir/.coveragerc"

cd "$sdk_dir" || exit 1

check_coverage() {
    local coverage_report
    local total_coverage

    mkdir -p "$report_dir"
    coverage_report=$(mktemp)

    if ! env PYTHONPATH="$sdk_dir" "$python_bin" -m coverage report --rcfile "$coverage_config" --skip-empty --fail-under "$coverage_threshold" > "$coverage_report" 2>&1; then
        cat "$coverage_report"
        rm -f "$coverage_report"
        exit 1
    fi

    cp "$coverage_report" "$report_dir/coverage_report.txt"

    total_coverage=$(env PYTHONPATH="$sdk_dir" "$python_bin" -c 'import pathlib, re, sys

text = pathlib.Path(sys.argv[1]).read_text()
match = re.search(r"TOTAL\s+.*?(\d+)%", text)

if not match:
    print("Could not parse coverage percentage.")
    sys.exit(1)

print(match.group(1))
' "$coverage_report") || {
        rm -f "$coverage_report"
        exit 1
    }

    rm -f "$coverage_report"
    echo "OK (${total_coverage}%)"
}

prepare_coverage_data() {
    env PYTHONPATH="$sdk_dir" "$python_bin" -m coverage erase --rcfile "$coverage_config"
}

combine_coverage_data() {
    if ! compgen -G "$sdk_dir/.coverage.*" >/dev/null; then
        return 0
    fi

    env PYTHONPATH="$sdk_dir" "$python_bin" -m coverage combine --rcfile "$coverage_config"
}

run_silent prepare_dev_environment

printf "resetting Ticket System Mock SDK coverage data... "
run_silent prepare_coverage_data

printf "running Ticket System Mock SDK unit tests with coverage... "
run_silent env PYTHONPATH="$sdk_dir" "$python_bin" -m coverage run --rcfile "$coverage_config" -m unittest "$sdk_dir/tests/tests_sdk.py"

printf "combining Ticket System Mock SDK coverage data... "
run_silent combine_coverage_data

printf "checking Ticket System Mock SDK coverage >= ${coverage_threshold}%%... "
check_coverage