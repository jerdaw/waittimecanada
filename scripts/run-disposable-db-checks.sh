#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.test.yml"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
DATABASE_URL="postgresql://waittime:waittime@127.0.0.1:54329/waittimecanada_test" # pragma: allowlist secret
NEXT_PUBLIC_MAPBOX_TOKEN="${NEXT_PUBLIC_MAPBOX_TOKEN:-pk.test.mock-token}"
NEXT_SMOKE_LOG="${TMPDIR:-/tmp}/waittimecanada-next-smoke.log"
NEXT_PID=""

export DATABASE_URL
export NEXT_PUBLIC_MAPBOX_TOKEN
export PLAYWRIGHT_PORT="${PLAYWRIGHT_PORT:-3000}"
export PLAYWRIGHT_BASE_URL="${PLAYWRIGHT_BASE_URL:-http://127.0.0.1:${PLAYWRIGHT_PORT}}"

cleanup() {
  if [[ -n "${NEXT_PID}" ]]; then
    kill "${NEXT_PID}" 2>/dev/null || true
    wait "${NEXT_PID}" 2>/dev/null || true
  fi

  if [[ "${KEEP_TEST_DB:-0}" != "1" ]] && docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" down -v >/dev/null 2>&1 || true
  fi
}

wait_for_postgres() {
  for _ in $(seq 1 60); do
    if docker compose -f "${COMPOSE_FILE}" exec -T postgres-test \
      pg_isready -U waittime -d waittimecanada_test >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "Timed out waiting for disposable PostgreSQL." >&2
  return 1
}

wait_for_url() {
  local url="$1"
  for _ in $(seq 1 60); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "Timed out waiting for ${url}. Next.js log: ${NEXT_SMOKE_LOG}" >&2
  return 1
}

use_project_node() {
  if [[ -s "${HOME}/.nvm/nvm.sh" ]]; then
    # Prefer the repo-supported Node major for local WSL runs. CI uses setup-node.
    # shellcheck source=/dev/null
    source "${HOME}/.nvm/nvm.sh"
    nvm use 22 >/dev/null
  fi
}

resolve_uv() {
  if [[ -n "${UV_BIN:-}" ]]; then
    if [[ -x "${UV_BIN}" ]]; then
      return 0
    fi

    echo "Configured UV_BIN is not executable: ${UV_BIN}" >&2
    exit 1
  fi

  if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
    return 0
  fi

  if [[ -x "${HOME}/.local/share/mise/shims/uv" ]]; then
    UV_BIN="${HOME}/.local/share/mise/shims/uv"
    return 0
  fi

  echo "uv is required for disposable DB checks." >&2
  exit 1
}

trap cleanup EXIT

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose is required for disposable DB checks." >&2
  exit 1
fi

docker compose -f "${COMPOSE_FILE}" up -d postgres-test
wait_for_postgres

cd "${BACKEND_DIR}"
resolve_uv
"${UV_BIN}" sync --locked --extra dev --python 3.12
"${UV_BIN}" run python run_migrations.py
"${UV_BIN}" run pytest tests/integration

cd "${FRONTEND_DIR}"
use_project_node
rm -rf node_modules
npm ci

if [[ "${SKIP_PLAYWRIGHT:-0}" != "1" ]]; then
  npx playwright install chromium
  if ! CI=1 npm run test:e2e -- --project=chromium --reporter=line; then
    echo "Playwright failed. If Chromium reported missing shared libraries, run:" >&2
    echo "  cd frontend && npx playwright install --with-deps chromium" >&2
    exit 1
  fi
else
  echo "Skipping Playwright because SKIP_PLAYWRIGHT=1."
fi

(
  cd "${FRONTEND_DIR}"
  npm run dev -- --hostname 127.0.0.1 --port 3000
) >"${NEXT_SMOKE_LOG}" 2>&1 &
NEXT_PID="$!"

wait_for_url "http://127.0.0.1:3000/api/health"

cd "${BACKEND_DIR}"
"${UV_BIN}" run pytest tests/e2e/test_pipeline.py
