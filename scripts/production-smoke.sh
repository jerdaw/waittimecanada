#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${PRODUCTION_BASE_URL:-${1:-}}"
TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-20}"

if [[ -z "${BASE_URL}" ]]; then
  echo "Usage: PRODUCTION_BASE_URL=https://example.com $0"
  echo "   or: $0 https://example.com"
  exit 2
fi

BASE_URL="${BASE_URL%/}"

failures=0

declare -a LEGACY_SOURCE_IDS=(
  "\"source_id\":\"manitoba-shared-health\""
  "\"source_id\":\"on-health\""
)

echo "Running production smoke checks against ${BASE_URL}"

check_route() {
  local path="$1"
  local marker="$2"
  shift 2
  local forbidden_markers=("$@")
  local url="${BASE_URL}${path}"
  body_file="$(mktemp)"

  if ! http_code="$(
    curl \
      --silent \
      --show-error \
      --location \
      --max-time "${TIMEOUT_SECONDS}" \
      --output "${body_file}" \
      --write-out "%{http_code}" \
      "${url}"
  )"; then
    echo "FAIL ${path} - request failed"
    failures=$((failures + 1))
    rm -f "${body_file}"
    return
  fi

  if [[ ! "${http_code}" =~ ^2[0-9]{2}$ ]]; then
    echo "FAIL ${path} - expected 2xx, got ${http_code}"
    failures=$((failures + 1))
    rm -f "${body_file}"
    return
  fi

  if ! grep -Fq "${marker}" "${body_file}"; then
    echo "FAIL ${path} - missing expected content: ${marker}"
    failures=$((failures + 1))
    rm -f "${body_file}"
    return
  fi

  for forbidden_marker in "${forbidden_markers[@]}"; do
    if grep -Fq "${forbidden_marker}" "${body_file}"; then
      echo "FAIL ${path} - found legacy source id: ${forbidden_marker}"
      failures=$((failures + 1))
      rm -f "${body_file}"
      return
    fi
  done

  echo "PASS ${path} (${http_code})"
  rm -f "${body_file}"
}

check_route "/" "Canadian ER Wait Time Data"
check_route "/methods" "Understanding Wait Time Metrics"
check_route "/data-quality" "Data Quality &amp; Provenance"
check_route "/analytics" "Analytics Dashboard"
check_route "/resources" "Safety alerts"
check_route "/api/health" "\"source_id\":\"ontario-health\"" "${LEGACY_SOURCE_IDS[@]}"
check_route "/api/resources/alerts?limit=1" "\"source_id\":\"health-canada-recalls\""
check_route "/api/resources?kind=aed&province=ON&limit=1" "\"kind\":\"aed\""
check_route "/api/resources?kind=facility&province=ON&q=Toronto%20General&limit=1" "Toronto General Hospital"
check_route "/api/resources/system-context?province=ON&limit=1" "\"source_id\":\"ontario-land-ambulance-response-times\""
check_route "/api/resources/aqhi?latitude=43.6532&longitude=-79.3832" "\"source_id\":\"aqhi-geomet\""
check_route "/api/status" "\"source_id\":\"ontario-health\"" "${LEGACY_SOURCE_IDS[@]}"
check_route "/api/data-quality" "\"source_id\":\"ontario-health\"" "${LEGACY_SOURCE_IDS[@]}"

if (( failures > 0 )); then
  echo "Smoke checks failed: ${failures}"
  exit 1
fi

echo "Smoke checks passed with no legacy source ids detected."
