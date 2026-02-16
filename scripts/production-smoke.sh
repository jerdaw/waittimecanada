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

declare -a PATHS=(
  "/"
  "/methods"
  "/data-quality"
  "/analytics"
)

declare -a EXPECTED_TEXT=(
  "WaitTime Canada"
  "Understanding Wait Time Metrics"
  "Data Quality & Provenance"
  "Analytics Dashboard"
)

failures=0

echo "Running production smoke checks against ${BASE_URL}"

for idx in "${!PATHS[@]}"; do
  path="${PATHS[$idx]}"
  marker="${EXPECTED_TEXT[$idx]}"
  url="${BASE_URL}${path}"
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
    continue
  fi

  if [[ ! "${http_code}" =~ ^2[0-9]{2}$ ]]; then
    echo "FAIL ${path} - expected 2xx, got ${http_code}"
    failures=$((failures + 1))
    rm -f "${body_file}"
    continue
  fi

  if ! grep -Fq "${marker}" "${body_file}"; then
    echo "FAIL ${path} - missing expected content: ${marker}"
    failures=$((failures + 1))
    rm -f "${body_file}"
    continue
  fi

  echo "PASS ${path} (${http_code})"
  rm -f "${body_file}"
done

if (( failures > 0 )); then
  echo "Smoke checks failed: ${failures}"
  exit 1
fi

echo "Smoke checks passed for ${#PATHS[@]} routes."
