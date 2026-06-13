#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
compose_file="${repo_root}/.devcontainer/development/docker-compose.yml"
command="${1:-start}"

usage() {
    cat <<'EOF'
Usage: scripts/run_n8n_smoke_test.bash [start|reload|stop|down|logs]

start  Stage the local n8n node package and recreate the profile-gated n8n service.
reload Re-stage the local n8n node package and recreate the running n8n service.
stop   Stop the local n8n service.
down   Remove the local n8n service and its containers.
logs   Follow the local n8n service logs.
EOF
}

require_docker_compose() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "docker is required" >&2
        exit 1
    fi
}

start_n8n() {
    mkdir -p "${repo_root}/.devcontainer/development/n8n/local-files"

    pushd "${repo_root}" >/dev/null
    ./scripts/build_n8n_dev_package.bash
    docker compose -f "${compose_file}" --profile n8n up -d --force-recreate --no-deps n8n
    docker compose -f "${compose_file}" ps n8n
    popd >/dev/null

    cat <<'EOF'
Local n8n smoke-test instance is available at http://localhost:5678
Use http://webapp:8000 as the API base URL inside the n8n credential.
EOF
}

reload_n8n() {
    pushd "${repo_root}" >/dev/null
    ./scripts/build_n8n_dev_package.bash
    docker compose -f "${compose_file}" --profile n8n up -d --force-recreate --no-deps n8n
    docker compose -f "${compose_file}" ps n8n
    popd >/dev/null
}

stop_n8n() {
    docker compose -f "${compose_file}" --profile n8n stop n8n
}

down_n8n() {
    docker compose -f "${compose_file}" --profile n8n down
}

logs_n8n() {
    docker compose -f "${compose_file}" --profile n8n logs -f n8n
}

require_docker_compose

case "${command}" in
    start)
        start_n8n
        ;;
    reload)
        reload_n8n
        ;;
    stop)
        stop_n8n
        ;;
    down)
        down_n8n
        ;;
    logs)
        logs_n8n
        ;;
    *)
        usage >&2
        exit 1
        ;;
esac