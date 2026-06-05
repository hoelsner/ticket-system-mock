#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
dockerfile_path="$repo_root/deploy/containers/webapp/Dockerfile"
bundle_script="$script_dir/create_build_bundle.bash"

default_commit_id="unknown"

if command -v git >/dev/null 2>&1; then
	default_commit_id="$(git -C "$repo_root" rev-parse --short=12 HEAD 2>/dev/null || printf 'unknown')"
fi

build_version="${1:-${BUILD_VERSION:-}}"
commit_id="${COMMIT_ID:-$default_commit_id}"
image_repository="${IMAGE_REPOSITORY:-itoperation-ticketing-demo-service}"
image_tag="${IMAGE_TAG:-}"
skip_docker_build="${SKIP_DOCKER_BUILD:-0}"

if [[ -z "$build_version" ]]; then
	build_version="$(date -u +%Y%m%d%H%M%S)-$commit_id"
fi

if [[ -z "$image_tag" ]]; then
	image_tag="$build_version"
fi

image_ref="${image_repository}:${image_tag}"

if [[ ! -f "$dockerfile_path" ]]; then
	echo "Dockerfile not found at $dockerfile_path"
	exit 1
fi

if [[ ! -x "$bundle_script" ]]; then
	echo "bundle script not found or not executable at $bundle_script"
	exit 1
fi

echo "build version: $build_version"
echo "commit id: $commit_id"
echo "image: $image_ref"

if [[ "$skip_docker_build" == "1" ]]; then
	echo "skipping docker build because SKIP_DOCKER_BUILD=1"
else
	if ! command -v docker >/dev/null 2>&1; then
		echo "docker is required to build the webapp image"
		exit 1
	fi

	docker build \
		-f "$dockerfile_path" \
		--build-arg "BUILD_VERSION=$build_version" \
		--build-arg "COMMIT_ID=$commit_id" \
		-t "$image_ref" \
		"$repo_root"
fi

"$bundle_script" "$build_version" "$image_ref" "$commit_id"

echo "finished build for $image_ref"
