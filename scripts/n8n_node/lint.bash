#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

run_silent prepare_environment

cd "$n8n_node_dir" || exit 1

printf "running n8n node typecheck... "
run_silent npm run typecheck

printf "running n8n node lint and complexity checks... "
run_silent npm run lint