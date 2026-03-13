#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
usage: scripts/release-vps-frontend.sh <ssh-target> [--deploy]

Creates a release from the current committed tree, uploads it to the VPS,
repoints /srv/apps/waittime-frontend/current, and optionally runs the
frontend VPS deploy script.

Environment overrides:
  WAITTIME_FRONTEND_VPS_APP_ROOT   default: /srv/apps/waittime-frontend
  WAITTIME_FRONTEND_VPS_ENV_FILE   default: /etc/projects-merge/env/waittime-frontend.env
EOF
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
fi

ssh_target="$1"
deploy_after_release="false"

if [[ $# -eq 2 ]]; then
  if [[ "$2" != "--deploy" ]]; then
    usage
  fi
  deploy_after_release="true"
fi

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
app_root="${WAITTIME_FRONTEND_VPS_APP_ROOT:-/srv/apps/waittime-frontend}"
env_file="${WAITTIME_FRONTEND_VPS_ENV_FILE:-/etc/projects-merge/env/waittime-frontend.env}"

if ! git -C "$repo_root" diff --quiet || ! git -C "$repo_root" diff --cached --quiet; then
  echo "working tree must be clean before creating a release" >&2
  exit 1
fi

revision="$(git -C "$repo_root" rev-parse --short HEAD)"
timestamp="$(date -u +%Y%m%d%H%M%S)"
release_dir="${app_root}/releases/${timestamp}-${revision}"

# shellcheck disable=SC2029
ssh "$ssh_target" "mkdir -p '$release_dir'"

# shellcheck disable=SC2029
git -C "$repo_root" archive --format=tar HEAD | ssh "$ssh_target" "tar -xf - -C '$release_dir'"

# shellcheck disable=SC2029
ssh "$ssh_target" "
  printf '%s\n' '$revision' > '$release_dir/REVISION' &&
  ln -sfn '$release_dir' '$app_root/current' &&
  printf 'CURRENT=%s\n' \"\$(readlink -f '$app_root/current')\" &&
  printf 'REVISION=%s\n' \"\$(cat '$app_root/current/REVISION')\"
"

if [[ "$deploy_after_release" == "true" ]]; then
  # shellcheck disable=SC2029
  ssh "$ssh_target" "
    cd '$app_root/current' &&
    ./scripts/deploy-vps-frontend.sh '$env_file'
  "
fi
