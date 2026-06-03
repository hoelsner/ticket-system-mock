#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

webapp_dir="${WEBAPP_DIR:-$repo_root/src/webapp}"
runtime_root="${DJANGO_RUNTIME_ROOT:-$repo_root/runtime}"
static_root="${DJANGO_STATIC_ROOT:-$runtime_root/static}"
media_root="${DJANGO_MEDIA_ROOT:-$runtime_root/media}"
cert_root="${DJANGO_CERT_ROOT:-$runtime_root/certificates}"
provisioning_dir="${DJANGO_PROVISIONING_DIR:-$runtime_root/provisioning}"
provisioning_flag="${DJANGO_PROVISIONING_FLAG:-$provisioning_dir/fixtures-loaded.flag}"
python_bin="${PYTHON_BIN:-$webapp_dir/.venv/bin/python3}"

if [[ ! -x "$python_bin" ]]; then
	python_bin="${PYTHON_BIN_FALLBACK:-python3}"
fi

if [[ ! -d "$webapp_dir" ]]; then
	echo "webapp directory not found at $webapp_dir"
	exit 1
fi

cd "$webapp_dir" || exit 1

mkdir -p "$static_root" "$media_root" "$cert_root" "$provisioning_dir"

export DJANGO_STATIC_ROOT="$static_root"
export DJANGO_MEDIA_ROOT="$media_root"

run_manage() {
	"$python_bin" manage.py "$@"
}

collect_fixture_files() {
	local fixture_dir="$webapp_dir/fixtures"

	if [[ ! -d "$fixture_dir" ]]; then
		return 0
	fi

	find "$fixture_dir" -maxdepth 1 -type f \( -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.xml' \) | sort
}

echo "running database migrations"
run_manage migrate --noinput

if [[ ! -f "$provisioning_flag" ]]; then
	echo "provisioning flag not found, checking initial fixtures"
	mapfile -t fixture_files < <(collect_fixture_files)

	if [[ ${#fixture_files[@]} -gt 0 ]]; then
		echo "loading initial fixtures"
		run_manage loaddata "${fixture_files[@]}"
	else
		echo "no initial fixtures found, skipping fixture loading"
	fi

	touch "$provisioning_flag"
	echo "wrote provisioning flag to $provisioning_flag"
else
	echo "provisioning flag found, skipping fixture loading"
fi

echo "collecting static files into $static_root"
run_manage collectstatic --noinput

echo "prepared shared runtime volume under $runtime_root"