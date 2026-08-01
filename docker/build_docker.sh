#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG=${1:-"$(whoami)/aagmf:latest"}
if [ "$#" -gt 0 ]; then
    shift
fi

PROJECT_ROOT="$(cd -- "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
DOCKERFILE_PATH="$PROJECT_ROOT/docker/Dockerfile"
EXTRA_BUILD_ARGS=()

if [ "$#" -gt 0 ]; then
    EXTRA_BUILD_ARGS=("$@")
fi

echo "Building Docker image $IMAGE_TAG from $DOCKERFILE_PATH"
docker build \
    --tag "$IMAGE_TAG" \
    --file "$DOCKERFILE_PATH" \
    "${EXTRA_BUILD_ARGS[@]}" \
    "$PROJECT_ROOT"
