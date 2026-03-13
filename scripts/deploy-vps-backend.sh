#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /path/to/env-file" >&2
  exit 1
fi

env_file="$1"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
backend_dir="${repo_root}/backend"
app_root="${WAITTIME_BACKEND_VPS_APP_ROOT:-/srv/apps/waittime-backend}"
venv_dir="${backend_dir}/.venv"
shared_dir="${app_root}/shared"
playwright_dir="${shared_dir}/playwright-browsers"

if [[ ! -f "$env_file" ]]; then
  echo "env file not found: $env_file" >&2
  exit 1
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

database_url="$(read_env_value "DATABASE_URL")"
if [[ -z "$database_url" ]]; then
  echo "env file must define DATABASE_URL" >&2
  exit 1
fi

mkdir -p "$shared_dir" "$playwright_dir"

python3 -m venv "$venv_dir"
"$venv_dir/bin/pip" install --upgrade pip
"$venv_dir/bin/pip" install -e "$backend_dir"
PLAYWRIGHT_BROWSERS_PATH="$playwright_dir" "$venv_dir/bin/playwright" install chromium

(
  cd "$backend_dir"
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
  PLAYWRIGHT_BROWSERS_PATH="$playwright_dir" "$venv_dir/bin/python" run_migrations.py
)

echo "backend_dir=${backend_dir}"
echo "venv_dir=${venv_dir}"
echo "playwright_browsers_path=${playwright_dir}"
echo "next_step=install or reload systemd timers if they are present"
