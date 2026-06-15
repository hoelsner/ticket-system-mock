#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

coverage_summary_file="$report_dir/coverage-summary.json"

run_silent prepare_environment

cd "$n8n_node_dir" || exit 1
mkdir -p "$report_dir"

printf "running n8n node unit tests with coverage... "

coverage_report=$(mktemp)
if ! npm run test:coverage > "$coverage_report" 2>&1; then
    cat "$coverage_report"
    rm -f "$coverage_report"
    exit 1
fi

cp "$coverage_report" "$report_dir/coverage_report.txt"
coverage_result=$(node -e 'const fs = require("node:fs"); const text = fs.readFileSync(process.argv[1], "utf8"); const match = text.match(/all files\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|/i); if (!match) { process.exit(1); } console.log(`${match[1]}% lines, ${match[2]}% branches`);' "$coverage_report") || {
    echo "could not parse coverage summary from $coverage_report"
    rm -f "$coverage_report"
    exit 1
}

rm -f "$coverage_report"
echo "OK (${coverage_result})"