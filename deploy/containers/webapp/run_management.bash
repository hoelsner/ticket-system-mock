#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

webapp_dir="${WEBAPP_DIR:-$repo_root/src/webapp}"
runtime_root="${DJANGO_RUNTIME_ROOT:-$repo_root/runtime}"
static_root="${DJANGO_STATIC_ROOT:-$runtime_root/static}"
media_root="${DJANGO_MEDIA_ROOT:-$runtime_root/media}"
cert_root="${DJANGO_CERT_ROOT:-$runtime_root/certificates}"
nginx_config_dir="${NGINX_CONFIG_DIR:-$runtime_root/nginx}"
nginx_config_file="${NGINX_CONFIG_FILE:-$nginx_config_dir/default.conf}"
provisioning_dir="${DJANGO_PROVISIONING_DIR:-$runtime_root/provisioning}"
provisioning_flag="${DJANGO_PROVISIONING_FLAG:-$provisioning_dir/fixtures-loaded.flag}"
bootstrap_fixtures="${DJANGO_BOOTSTRAP_FIXTURES:-initial_data}"
static_fixtures="${DJANGO_STATIC_FIXTURES:-static_data}"
python_bin="${PYTHON_BIN:-$webapp_dir/.venv/bin/python3}"
nginx_server_name="${NGINX_SERVER_NAME:-_}"
nginx_client_max_body_size="${NGINX_CLIENT_MAX_BODY_SIZE:-10m}"
fixture_extensions=("json" "yaml" "yml" "xml")

if [[ ! -x "$python_bin" ]]; then
	python_bin="${PYTHON_BIN_FALLBACK:-python3}"
fi

if [[ ! -d "$webapp_dir" ]]; then
	echo "webapp directory not found at $webapp_dir"
	exit 1
fi

cd "$webapp_dir" || exit 1

mkdir -p "$static_root" "$media_root" "$cert_root" "$nginx_config_dir" "$provisioning_dir"

export DJANGO_STATIC_ROOT="$static_root"
export DJANGO_MEDIA_ROOT="$media_root"

run_manage() {
	"$python_bin" manage.py "$@"
}

trim_whitespace() {
	local value="$1"

	value="${value#"${value%%[![:space:]]*}"}"
	value="${value%"${value##*[![:space:]]}"}"
	printf '%s\n' "$value"
}

fixture_label_exists() {
	local label="$1"
	local extension

	for extension in "${fixture_extensions[@]}"; do
		if [[ -f "$webapp_dir/fixtures/$label.$extension" ]]; then
			return 0
		fi
	done

	return 1
}

collect_existing_fixture_labels() {
	local labels_csv="$1"
	local raw_labels=()
	local existing_labels=()
	local raw_label
	local label

	IFS=',' read -r -a raw_labels <<< "$labels_csv"

	for raw_label in "${raw_labels[@]}"; do
		label="$(trim_whitespace "$raw_label")"

		if [[ -z "$label" ]]; then
			continue
		fi

		if fixture_label_exists "$label"; then
			existing_labels+=("$label")
		else
			echo "fixture '$label' not found in $webapp_dir/fixtures, skipping" >&2
		fi
	done

	printf '%s\n' "${existing_labels[@]}"
}

load_fixture_labels() {
	local scope="$1"
	shift
	local labels=("$@")

	if [[ ${#labels[@]} -eq 0 ]]; then
		echo "no $scope fixtures found, skipping"
		return 0
	fi

	echo "loading $scope fixtures: ${labels[*]}"
	run_manage loaddata "${labels[@]}"
}

generate_self_signed_certificate() {
	local service_name="$1"
	local certificate_file="$cert_root/${service_name}.crt"
	local private_key_file="$cert_root/${service_name}.key"

	if [[ -f "$certificate_file" && -f "$private_key_file" ]]; then
		echo "$service_name certificate already exists, skipping generation"
		return 0
	fi

	if ! command -v openssl >/dev/null 2>&1; then
		echo "openssl is required to generate the $service_name self-signed certificate"
		exit 1
	fi

	echo "generating self-signed certificate for $service_name"
	openssl req \
		-x509 \
		-nodes \
		-newkey rsa:2048 \
		-keyout "$private_key_file" \
		-out "$certificate_file" \
		-days 3650 \
		-subj "/CN=localhost" \
		-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
	chmod 600 "$private_key_file"
	chmod 644 "$certificate_file"
}

generate_nginx_configuration() {
	echo "writing nginx configuration to $nginx_config_file"
	cat >"$nginx_config_file" <<EOF
upstream django_upstream {
	server webapp:8000;
}

server {
	listen 80;
	server_name $nginx_server_name;
	return 301 https://\$host\$request_uri;
}

server {
	listen 443 ssl;
	server_name $nginx_server_name;
	client_max_body_size $nginx_client_max_body_size;
	ssl_certificate $cert_root/nginx.crt;
	ssl_certificate_key $cert_root/nginx.key;

	location /static/ {
		alias $static_root/;
		access_log off;
		expires 1h;
		add_header Cache-Control "public";
	}

	location /media/ {
		alias $media_root/;
		access_log off;
		expires 1h;
		add_header Cache-Control "public";
	}

	location / {
		proxy_pass http://django_upstream;
		proxy_http_version 1.1;
		proxy_set_header Host \$host;
		proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto https;
		proxy_set_header X-Real-IP \$remote_addr;
	}
}
EOF
}

echo "running database migrations"
run_manage migrate --noinput

generate_self_signed_certificate "gunicorn"
generate_self_signed_certificate "nginx"
generate_nginx_configuration

if [[ ! -f "$provisioning_flag" ]]; then
	echo "provisioning flag not found, loading bootstrap fixtures"
	mapfile -t bootstrap_fixture_labels < <(collect_existing_fixture_labels "$bootstrap_fixtures")
	load_fixture_labels "bootstrap" "${bootstrap_fixture_labels[@]}"

	touch "$provisioning_flag"
	echo "wrote provisioning flag to $provisioning_flag"
else
	echo "provisioning flag found, skipping bootstrap fixtures"
fi

mapfile -t static_fixture_labels < <(collect_existing_fixture_labels "$static_fixtures")
load_fixture_labels "static" "${static_fixture_labels[@]}"

echo "collecting static files into $static_root"
run_manage collectstatic --noinput

echo "prepared shared runtime volume under $runtime_root"