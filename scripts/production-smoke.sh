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

check_homepage_coverage() {
  local hospitals_file homepage_file hospital_count province_count
  hospitals_file="$(mktemp)"
  homepage_file="$(mktemp)"

  if ! curl --silent --show-error --location --max-time "${TIMEOUT_SECONDS}" \
    --output "${hospitals_file}" "${BASE_URL}/api/hospitals"; then
    echo "FAIL homepage coverage - hospital API request failed"
    failures=$((failures + 1))
    rm -f "${hospitals_file}" "${homepage_file}"
    return
  fi

  hospital_count="$(jq -er '.coverage.hospital_count' "${hospitals_file}")" || {
    echo "FAIL homepage coverage - missing hospital_count"
    failures=$((failures + 1))
    rm -f "${hospitals_file}" "${homepage_file}"
    return
  }
  province_count="$(jq -er '.coverage.province_count' "${hospitals_file}")" || {
    echo "FAIL homepage coverage - missing province_count"
    failures=$((failures + 1))
    rm -f "${hospitals_file}" "${homepage_file}"
    return
  }

  if ! curl --silent --show-error --location --max-time "${TIMEOUT_SECONDS}" \
    --output "${homepage_file}" "${BASE_URL}/en"; then
    echo "FAIL homepage coverage - homepage request failed"
    failures=$((failures + 1))
    rm -f "${hospitals_file}" "${homepage_file}"
    return
  fi

  if ! grep -Fq "${province_count} Provinces" "${homepage_file}" || \
    ! grep -Fq "${hospital_count} Hospitals" "${homepage_file}" || \
    ! grep -Fq "Sources Checked Hourly" "${homepage_file}"; then
    echo "FAIL homepage coverage - SSR count or cadence label does not match API coverage"
    failures=$((failures + 1))
  elif grep -Fq "...+ Hospitals" "${homepage_file}" || \
    grep -Fq "Fresh Data Every 4 Hours" "${homepage_file}"; then
    echo "FAIL homepage coverage - legacy placeholder or cadence label is present"
    failures=$((failures + 1))
  else
    echo "PASS homepage coverage (${province_count} provinces, ${hospital_count} hospitals)"
  fi

  rm -f "${hospitals_file}" "${homepage_file}"
}

check_route "/" "Canadian ER Wait Time Data"
check_homepage_coverage
check_route "/methods" "Understanding Wait Time Metrics"
check_route "/data-quality" "Data Quality &amp; Provenance"
check_route "/analytics" "Analytics Dashboard"
check_route "/resources" "Safety alerts"
check_route "/api/health" "\"source_id\":\"ontario-health\"" "${LEGACY_SOURCE_IDS[@]}"
check_route "/api/resources/alerts?limit=1" "\"source_id\":\"health-canada-recalls\""
check_route "/api/resources?kind=aed&province=ON&limit=1" "\"kind\":\"aed\""
check_route "/api/resources?kind=facility&province=ON&q=Toronto%20General&limit=1" "Toronto General Hospital"
check_route "/api/resources/system-context?province=ON&limit=1" "\"source_id\":\"ontario-land-ambulance-response-times\""
check_route "/api/resources/water-advisories?province=ON&limit=1" "\"source_id\":\"isc-drinking-water-advisories\""
check_route "/api/resources/aqhi?latitude=43.6532&longitude=-79.3832" "\"source_id\":\"aqhi-geomet\""
check_route "/api/status" "\"overall_status_basis\":\"measurement_hour_completeness_24h\"" "${LEGACY_SOURCE_IDS[@]}"
check_route "/api/data-quality" "\"source_id\":\"ontario-health\"" "${LEGACY_SOURCE_IDS[@]}"

if (( failures > 0 )); then
  echo "Smoke checks failed: ${failures}"
  exit 1
fi

echo "Smoke checks passed with no legacy source ids detected."
