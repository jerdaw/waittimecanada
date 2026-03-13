#!/usr/bin/env bash
set -euo pipefail

enable_timers="false"
enable_cleanup="false"
run_user="${WAITTIME_BACKEND_RUN_USER:-$(id -un)}"
run_group="${WAITTIME_BACKEND_RUN_GROUP:-$(id -gn)}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --enable)
      enable_timers="true"
      shift
      ;;
    --enable-cleanup)
      enable_cleanup="true"
      shift
      ;;
    --user)
      run_user="$2"
      shift 2
      ;;
    --group)
      run_group="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
template_dir="${repo_root}/backend/systemd"
target_dir="/etc/systemd/system"

install_template() {
  local template_name="$1"
  local unit_name="${template_name%.template}"

  sed \
    -e "s/__WAITTIME_USER__/${run_user}/g" \
    -e "s/__WAITTIME_GROUP__/${run_group}/g" \
    "${template_dir}/${template_name}" | sudo tee "${target_dir}/${unit_name}" >/dev/null
}

install_file() {
  local filename="$1"
  sudo install -m 0644 "${template_dir}/${filename}" "${target_dir}/${filename}"
}

install_template "waittime-backend-scraper.service.template"
install_file "waittime-backend-scraper.timer"
install_template "waittime-backend-heartbeat.service.template"
install_file "waittime-backend-heartbeat.timer"
install_template "waittime-backend-quality-snapshot.service.template"
install_file "waittime-backend-quality-snapshot.timer"
install_template "waittime-backend-database-cleanup.service.template"
install_file "waittime-backend-database-cleanup.timer"

sudo systemctl daemon-reload

if [[ "$enable_timers" == "true" ]]; then
  sudo systemctl enable --now \
    waittime-backend-scraper.timer \
    waittime-backend-heartbeat.timer \
    waittime-backend-quality-snapshot.timer
fi

if [[ "$enable_cleanup" == "true" ]]; then
  sudo systemctl enable --now waittime-backend-database-cleanup.timer
fi

echo "Installed backend systemd units for user=${run_user} group=${run_group}"
if [[ "$enable_timers" == "true" ]]; then
  echo "Enabled timers: scraper, heartbeat, quality snapshot"
fi
if [[ "$enable_cleanup" == "true" ]]; then
  echo "Enabled timer: database cleanup"
fi
