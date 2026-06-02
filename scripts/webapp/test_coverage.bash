#!/bin/bash
#
# This script runs the unit tests for the web application with coverage. It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
webapp_dir="$repo_root/src/webapp"
python_bin="$webapp_dir/.venv/bin/python3"
report_dir="$webapp_dir/covreport"
coverage_config="$webapp_dir/.coveragerc"
coverage_threshold=98

cd "$webapp_dir" || exit 1

if [[ ! -x "$python_bin" ]]; then
    echo "python interpreter not found at $python_bin"
    exit 1
fi

if [[ ! -f "$coverage_config" ]]; then
    echo "coverage configuration not found at $coverage_config"
    exit 1
fi

if ! "$python_bin" -m coverage --version >/dev/null 2>&1; then
    echo "coverage is not available in the webapp virtual environment"
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

check_coverage() {
    local coverage_report
    local total_coverage

    mkdir -p "$report_dir"
    coverage_report=$(mktemp)

    if ! "$python_bin" -m coverage report --rcfile "$coverage_config" --skip-empty --fail-under "$coverage_threshold" > "$coverage_report" 2>&1; then
        cat "$coverage_report"
        rm -f "$coverage_report"
        exit 1
    fi

    cp "$coverage_report" "$report_dir/coverage_report.txt"

    total_coverage=$("$python_bin" -c 'import pathlib, re, sys

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
    "$python_bin" -m coverage erase --rcfile "$coverage_config"
}

combine_coverage_data() {
    "$python_bin" -m coverage combine --rcfile "$coverage_config"
}

printf "resetting coverage data... "
run_silent prepare_coverage_data

printf "running unit tests with coverage... "
run_silent env "$python_bin" -m coverage run --rcfile "$coverage_config" manage.py test --noinput

printf "combining coverage data... "
run_silent combine_coverage_data

printf "checking coverage >= ${coverage_threshold}%%... "
check_coverage