#!/bin/bash
#
# This script runs complexity checks for the web application. It should be run from the root of the repository.
#
set -o pipefail

threshold=2.0
exclude_pattern="**/test_*.py,**/tests/**"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
webapp_dir="$repo_root/src/webapp"
python_bin="$webapp_dir/.venv/bin/python3"
report_dir="$webapp_dir/covreport"

cd "$webapp_dir" || exit 1

if [[ ! -x "$python_bin" ]]; then
    echo "python interpreter not found at $python_bin"
    exit 1
fi

if ! "$python_bin" -m radon --help >/dev/null 2>&1; then
    echo "radon is not available in the webapp virtual environment"
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

check_average_complexity() {
    local avg_report
    local average_complexity
    avg_report=$(mktemp)

    if ! "$python_bin" -m radon cc . -a -s --exclude "$exclude_pattern" > "$avg_report" 2>&1; then
        cat "$avg_report"
        rm -f "$avg_report"
        exit 1
    fi

    average_complexity=$("$python_bin" -c 'import pathlib, re, sys

threshold = float(sys.argv[1])
report_path = pathlib.Path(sys.argv[2])
text = report_path.read_text()
match = re.search(r"Average complexity: [A-F] \(([\d.]+)\)", text)

if not match:
    print("Could not parse average complexity.")
    sys.exit(1)

value = float(match.group(1))
if value > threshold:
    print(f"avg complexity at {value} which is too high (threshold {threshold})")
    sys.exit(1)
print(value)
' "$threshold" "$avg_report") || {
        rm -f "$avg_report"
        exit 1
    }

    rm -f "$avg_report"
    echo "OK (${average_complexity})"
}

check_individual_complexity() {
    local complexity_report
    complexity_report=$(mktemp)

    if ! "$python_bin" -m radon cc -s -j . > "$complexity_report" 2>&1; then
        cat "$complexity_report"
        rm -f "$complexity_report"
        exit 1
    fi

    if ! "$python_bin" -c 'import json, pathlib, sys

report_path = pathlib.Path(sys.argv[1])
data = json.loads(report_path.read_text())
max_allowed = {"A", "B"}
failures = []

for path, items in data.items():
    for entry in items:
        if entry["rank"] not in max_allowed:
            failures.append(f"{path}: {entry['name']} has complexity {entry['complexity']} ({entry['rank']})")

if failures:
    print("Cyclomatic complexity threshold exceeded:")
    for failure in failures:
        print(f" - {failure}")
    sys.exit(1)
' "$complexity_report"; then
        rm -f "$complexity_report"
        exit 1
    fi

    rm -f "$complexity_report"
    echo "OK"
}

generate_reports() {
    mkdir -p "$report_dir"

    "$python_bin" -m radon cc . -a -s --exclude "$exclude_pattern" --md --output-file "$report_dir/radon_cc_report.md" &&
        "$python_bin" -m radon mi . -s --exclude "$exclude_pattern" --sort --output-file "$report_dir/radon_mi_report.txt" &&
        "$python_bin" -m radon raw . -s --exclude "$exclude_pattern" --output-file "$report_dir/radon_raw_report.txt"
}

printf "checking average complexity... "
check_average_complexity

printf "checking per-function complexity... "
check_individual_complexity

printf "generating complexity reports... "
run_silent generate_reports
