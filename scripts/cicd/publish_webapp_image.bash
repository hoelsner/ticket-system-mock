#!/bin/bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
dockerfile_path="$repo_root/deploy/containers/webapp/Dockerfile"
default_commit_id="unknown"

if command -v git >/dev/null 2>&1; then
	default_commit_id="$(git -C "$repo_root" rev-parse --short=12 HEAD 2>/dev/null || printf 'unknown')"
fi

image_repository="${IMAGE_REPOSITORY:-hoelsner/ticket-system-mock}"
image_tag="${IMAGE_TAG:-latest}"
image_platforms="${IMAGE_PLATFORMS:-linux/amd64,linux/arm64}"
build_version="${BUILD_VERSION:-$image_tag}"
commit_id="${COMMIT_ID:-$default_commit_id}"
image_ref="${image_repository}:${image_tag}"

if [[ ! -f "$dockerfile_path" ]]; then
	echo "Dockerfile not found at $dockerfile_path"
	exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
	echo "docker is required to publish the webapp image"
	exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
	echo "docker buildx is required to publish the webapp image"
	exit 1
fi

echo "build version: $build_version"
echo "commit id: $commit_id"
echo "image: $image_ref"
echo "platforms: $image_platforms"

docker buildx build \
	-f "$dockerfile_path" \
	--platform "$image_platforms" \
	--build-arg "BUILD_VERSION=$build_version" \
	--build-arg "COMMIT_ID=$commit_id" \
	-t "$image_ref" \
	--push \
	"$repo_root"

echo "published $image_ref"
