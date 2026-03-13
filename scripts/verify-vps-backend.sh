#!/usr/bin/env bash
set -euo pipefail

app_root="${WAITTIME_BACKEND_VPS_APP_ROOT:-/srv/apps/waittime-backend}"
env_file="${WAITTIME_BACKEND_VPS_ENV_FILE:-/etc/projects-merge/env/waittime-backend.env}"
venv_python="${app_root}/current/backend/.venv/bin/python"
playwright_dir="${app_root}/shared/playwright-browsers"

required_timers=(
  "waittime-backend-scraper.timer"
  "waittime-backend-heartbeat.timer"
  "waittime-backend-quality-snapshot.timer"
)

echo "WaitTime backend VPS verification"
echo

if [[ ! -f "$env_file" ]]; then
  echo "FAIL missing env file: $env_file"
  exit 1
fi

if [[ ! -x "$venv_python" ]]; then
  echo "FAIL missing backend venv python: $venv_python"
  exit 1
fi

if [[ ! -d "$playwright_dir" ]]; then
  echo "FAIL missing Playwright browser cache dir: $playwright_dir"
  exit 1
fi

for timer in "${required_timers[@]}"; do
  if systemctl is-enabled "$timer" >/dev/null 2>&1; then
    echo "OK   enabled $timer"
  else
    echo "FAIL $timer is not enabled"
    exit 1
  fi

  if systemctl is-active "$timer" >/dev/null 2>&1; then
    echo "OK   active  $timer"
  else
    echo "FAIL $timer is not active"
    exit 1
  fi
done

echo
systemctl list-timers 'waittime-backend-*' --all || true

echo
echo "Running heartbeat dry-run..."
sudo systemd-run --wait --pipe \
  --property="EnvironmentFile=${env_file}" \
  --property="WorkingDirectory=${app_root}/current/backend" \
  --setenv="PLAYWRIGHT_BROWSERS_PATH=${playwright_dir}" \
  "${venv_python}" -m waittime.cli.check_heartbeat --max-age 120 --dry-run --verbose
