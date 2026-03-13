#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /path/to/env-file" >&2
  exit 1
fi

env_file="$1"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
frontend_dir="${repo_root}/frontend"
image_name="waittime-frontend"
container_name="waittime-frontend"
host_bind="127.0.0.1:3400:3000"

if [[ ! -f "$env_file" ]]; then
  echo "env file not found: $env_file" >&2
  exit 1
fi

if git_revision="$(git -C "$repo_root" rev-parse --short HEAD 2>/dev/null)"; then
  tag="$git_revision"
elif [[ -f "$repo_root/REVISION" ]]; then
  tag="$(tr -d '[:space:]' < "$repo_root/REVISION")"
else
  tag="$(date -u +%Y%m%d%H%M%S)"
fi

read_env_value() {
  local key="$1"
  local value
  value="$(grep -E "^${key}=" "$env_file" | tail -n 1 | cut -d= -f2- || true)"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "$value"
}

next_public_mapbox_token="$(read_env_value "NEXT_PUBLIC_MAPBOX_TOKEN")"
next_public_base_url="$(read_env_value "NEXT_PUBLIC_BASE_URL")"

if [[ -z "$next_public_mapbox_token" ]]; then
  echo "env file must define NEXT_PUBLIC_MAPBOX_TOKEN" >&2
  exit 1
fi

if [[ -z "$next_public_base_url" ]]; then
  next_public_base_url="https://wait-time.ca"
fi

build_args=(
  "--build-arg" "NEXT_PUBLIC_BASE_URL=${next_public_base_url}"
  "--build-arg" "NEXT_PUBLIC_MAPBOX_TOKEN=${next_public_mapbox_token}"
)

if docker buildx version >/dev/null 2>&1; then
  docker buildx build --load "${build_args[@]}" -t "${image_name}:${tag}" "$frontend_dir"
else
  echo "warning: docker buildx not available; falling back to legacy docker build" >&2
  docker build "${build_args[@]}" -t "${image_name}:${tag}" "$frontend_dir"
fi

if docker ps -a --format '{{.Names}}' | grep -Fxq "$container_name"; then
  docker rm -f "$container_name" >/dev/null
fi

docker run -d \
  --name "$container_name" \
  --restart unless-stopped \
  --env-file "$env_file" \
  -e "APP_VERSION=$tag" \
  -p "$host_bind" \
  "${image_name}:${tag}"

echo "container=${container_name}"
echo "image=${image_name}:${tag}"
echo "health_url=http://127.0.0.1:3400/api/health"
