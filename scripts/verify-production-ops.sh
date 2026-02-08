#!/usr/bin/env bash
set -euo pipefail

repo="${1:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI is required. Install from https://cli.github.com/"
  exit 2
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh auth is required. Run: gh auth login"
  exit 2
fi

if [[ -z "${repo}" ]]; then
  repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
fi

echo "Production ops audit for ${repo}"
echo

declare -a required_secrets=(
  "DATABASE_URL"
)

declare -a recommended_secrets=(
  "PUSHOVER_USER_KEY"
  "PUSHOVER_API_TOKEN"
  "PRODUCTION_BASE_URL"
)

declare -a required_workflows=(
  "scraper-cron.yml"
  "heartbeat-monitor.yml"
)

declare -a recommended_workflows=(
  "production-smoke.yml"
)

# Age thresholds allow for normal GitHub Actions schedule jitter.
declare -a required_runs=(
  "scraper-cron.yml:75"
  "heartbeat-monitor.yml:90"
)

is_present() {
  local needle="$1"
  shift
  local value
  for value in "$@"; do
    if [[ "${value}" == "${needle}" ]]; then
      return 0
    fi
  done
  return 1
}

minutes_since_timestamp() {
  local timestamp="$1"
  python3 - "$timestamp" <<'PY'
from datetime import datetime, timezone
import sys

ts = sys.argv[1]
dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
age = datetime.now(timezone.utc) - dt
print(int(age.total_seconds() // 60))
PY
}

mapfile -t secret_names < <(gh secret list --repo "${repo}" --json name --jq '.[].name')

echo "Secrets:"
missing_required=0

for secret in "${required_secrets[@]}"; do
  if is_present "${secret}" "${secret_names[@]}"; then
    echo "  OK   ${secret}"
  else
    echo "  FAIL ${secret} (required)"
    missing_required=1
  fi
done

for secret in "${recommended_secrets[@]}"; do
  if is_present "${secret}" "${secret_names[@]}"; then
    echo "  OK   ${secret}"
  else
    echo "  WARN ${secret} (recommended)"
  fi
done

echo
echo "Workflow States:"
workflow_failures=0
workflow_warnings=0

for workflow in "${required_workflows[@]}"; do
  state="$(gh api "repos/${repo}/actions/workflows/${workflow}" --jq .state 2>/dev/null || true)"
  if [[ "${state}" == "active" ]]; then
    echo "  OK   ${workflow} is active"
  elif [[ -z "${state}" ]]; then
    echo "  FAIL ${workflow} not found"
    workflow_failures=1
  else
    echo "  FAIL ${workflow} state=${state}"
    workflow_failures=1
  fi
done

for workflow in "${recommended_workflows[@]}"; do
  state="$(gh api "repos/${repo}/actions/workflows/${workflow}" --jq .state 2>/dev/null || true)"
  if [[ "${state}" == "active" ]]; then
    echo "  OK   ${workflow} is active"
  elif [[ -z "${state}" ]]; then
    echo "  WARN ${workflow} not found (recommended)"
    workflow_warnings=1
  else
    echo "  WARN ${workflow} state=${state} (recommended)"
    workflow_warnings=1
  fi
done

echo
echo "Recent Run Freshness:"
run_failures=0

for check in "${required_runs[@]}"; do
  workflow="${check%%:*}"
  max_age="${check##*:}"
  run_json="$(gh run list --repo "${repo}" --workflow "${workflow}" --limit 1 --json status,conclusion,createdAt,url)"
  run_fields="$(python3 - "${run_json}" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
if not payload:
    print("|||")
    raise SystemExit(0)

latest = payload[0]
created_at = latest.get("createdAt", "")
status = latest.get("status", "")
conclusion = latest.get("conclusion", "")
url = latest.get("url", "")
print(f"{created_at}|{status}|{conclusion}|{url}")
PY
)"

  IFS="|" read -r created_at status conclusion run_url <<<"${run_fields}"

  if [[ -z "${created_at}" ]]; then
    echo "  FAIL ${workflow} has no runs"
    run_failures=1
    continue
  fi

  age_minutes="$(minutes_since_timestamp "${created_at}")"

  if [[ "${status}" != "completed" ]]; then
    if (( age_minutes > max_age )); then
      echo "  FAIL ${workflow} latest run still ${status} after ${age_minutes}m (>${max_age}m)"
      if [[ -n "${run_url}" ]]; then
        echo "       ${run_url}"
      fi
      run_failures=1
      continue
    fi
    echo "  OK   ${workflow} latest run is ${status} (${age_minutes}m ago)"
    continue
  fi

  if [[ "${conclusion}" != "success" ]]; then
    echo "  FAIL ${workflow} latest run not successful (status=${status}, conclusion=${conclusion})"
    if [[ -n "${run_url}" ]]; then
      echo "       ${run_url}"
    fi
    run_failures=1
    continue
  fi

  if (( age_minutes > max_age )); then
    echo "  FAIL ${workflow} latest success is stale (${age_minutes}m > ${max_age}m)"
    if [[ -n "${run_url}" ]]; then
      echo "       ${run_url}"
    fi
    run_failures=1
    continue
  fi

  echo "  OK   ${workflow} latest success ${age_minutes}m ago"
done

echo
if (( missing_required == 0 && workflow_failures == 0 && run_failures == 0 )); then
  if (( workflow_warnings != 0 )); then
    echo "Production ops audit passed with warnings."
  else
    echo "Production ops audit passed."
  fi
  exit 0
fi

echo "Production ops audit failed."
exit 1
