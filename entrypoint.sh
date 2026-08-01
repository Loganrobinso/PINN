#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

DOCKER_IMAGE_NAME=${DOCKER_IMAGE_NAME:-"$(whoami)/heat-pinn:latest"}
DOCKERFILE_PATH="docker/Dockerfile"
REQUIREMENTS_PATH="requirements.txt"
HASH_FILE=".docker_hashes"

HOST_DATA_DIR=${HOST_DATA_DIR:-/data}
SHM_SIZE=${SHM_SIZE:-8g}
EXTRA_DOCKER_FLAGS=${EXTRA_DOCKER_FLAGS:-}

compute_hashes() {
    DOCKERFILE_HASH=$(md5sum "$DOCKERFILE_PATH" | awk '{print $1}')
    REQUIREMENTS_HASH=$(md5sum "$REQUIREMENTS_PATH" | awk '{print $1}')
}

write_hashes() {
    echo "$DOCKERFILE_HASH $REQUIREMENTS_HASH" > "$HASH_FILE"
}

rebuild_docker_image() {
    echo "Rebuilding Docker image: $DOCKER_IMAGE_NAME"
    ./docker/build_docker.sh "$DOCKER_IMAGE_NAME"
}

ensure_image() {
    compute_hashes
    if ! docker image inspect "$DOCKER_IMAGE_NAME" >/dev/null 2>&1; then
        echo "Docker image does not exist locally. Building..."
        rebuild_docker_image
        write_hashes
        return
    fi

    if [ -f "$HASH_FILE" ]; then
        read -r OLD_DOCKERFILE_HASH OLD_REQUIREMENTS_HASH < "$HASH_FILE"
    else
        OLD_DOCKERFILE_HASH=""
        OLD_REQUIREMENTS_HASH=""
    fi

    if [ "$DOCKERFILE_HASH" != "$OLD_DOCKERFILE_HASH" ] || [ "$REQUIREMENTS_HASH" != "$OLD_REQUIREMENTS_HASH" ]; then
        echo "Detected Dockerfile/requirements changes. Rebuilding image..."
        rebuild_docker_image
    else
        echo "Docker image is up to date."
    fi

    write_hashes
}

ensure_image

TTY_FLAG=()
if [ -t 0 ] && [ -t 1 ]; then
    TTY_FLAG=(-it)
fi

GPU_FLAG=()
if command -v nvidia-smi >/dev/null 2>&1 && docker info 2>/dev/null | grep -qi nvidia; then
    GPU_FLAG=(--gpus all)
elif command -v nvidia-smi >/dev/null 2>&1; then
    echo "nvidia-smi found but Docker's NVIDIA runtime isn't configured; running on CPU." >&2
fi

RUN_ARGS=(
    "${GPU_FLAG[@]}"
    --shm-size="$SHM_SIZE"
    --volume "$PROJECT_ROOT:/app"
    --rm
    --user "$(id -u):$(id -g)"
    -e GEMINI_API_KEY="${GEMINI_API_KEY:-}"
    -e HF_TOKEN="${HF_TOKEN:-}"
    "${TTY_FLAG[@]}"
)

if [ -d "$HOST_DATA_DIR" ]; then
    RUN_ARGS+=(--volume "$HOST_DATA_DIR:/data")
fi

if [ -n "$EXTRA_DOCKER_FLAGS" ]; then
    # shellcheck disable=SC2206
    read -r -a EXTRA_FLAGS_ARRAY <<<"$EXTRA_DOCKER_FLAGS"
    RUN_ARGS+=("${EXTRA_FLAGS_ARRAY[@]}")
fi

CONTAINER_CMD=()
if [ "$#" -gt 0 ]; then
    CONTAINER_CMD=("$@")
fi

docker run "${RUN_ARGS[@]}" "$DOCKER_IMAGE_NAME" "${CONTAINER_CMD[@]}"
