#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/common.bash"

printf "building n8n node package... "
run_silent prepare_environment

cd "$n8n_node_dir" || exit 1
run_silent npm run build