#!/bin/bash
#
# This script runs complexity checks for the Ticket System Mock Python SDK.
# It should be run from the root of the repository.
#
set -o pipefail

threshold=2.0
exclude_pattern="**/test_*.py,**/tests/**,**/.venv/**"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

cd "$sdk_dir" || exit 1

check_average_complexity() {
    local avg_report
    local average_complexity
    avg_report=$(mktemp)

    if ! env PYTHONPATH="$sdk_dir" "$python_bin" -m radon cc ticketsystemmock -a -s --exclude "$exclude_pattern" > "$avg_report" 2>&1; then
        cat "$avg_report"
        rm -f "$avg_report"
        exit 1
    fi

    average_complexity=$(env PYTHONPATH="$sdk_dir" "$python_bin" -c 'import pathlib, re, sys

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

    if ! env PYTHONPATH="$sdk_dir" "$python_bin" -m radon cc -s -j ticketsystemmock > "$complexity_report" 2>&1; then
        cat "$complexity_report"
        rm -f "$complexity_report"
        exit 1
    fi

    if ! env PYTHONPATH="$sdk_dir" "$python_bin" -c 'import json, pathlib, sys

report_path = pathlib.Path(sys.argv[1])
data = json.loads(report_path.read_text())
max_allowed = {"A", "B"}
failures = []

for path, items in data.items():
    for entry in items:
        if entry["rank"] not in max_allowed:
            failures.append(
                "{}: {} has complexity {} ({})".format(
                    path,
                    entry["name"],
                    entry["complexity"],
                    entry["rank"],
                )
            )

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

    env PYTHONPATH="$sdk_dir" "$python_bin" -m radon cc ticketsystemmock -a -s --exclude "$exclude_pattern" --md --output-file "$report_dir/radon_cc_report.md" &&
        env PYTHONPATH="$sdk_dir" "$python_bin" -m radon mi ticketsystemmock -s --exclude "$exclude_pattern" --sort --output-file "$report_dir/radon_mi_report.txt" &&
        env PYTHONPATH="$sdk_dir" "$python_bin" -m radon raw ticketsystemmock -s --exclude "$exclude_pattern" --output-file "$report_dir/radon_raw_report.txt"
}

run_silent prepare_dev_environment

printf "checking Ticket System Mock SDK average complexity... "
check_average_complexity

printf "checking Ticket System Mock SDK per-function complexity... "
check_individual_complexity

printf "generating Ticket System Mock SDK complexity reports... "
run_silent generate_reports