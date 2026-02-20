#!/usr/bin/env bash

set -euo pipefail

current_ref="${COMMIT_REF:-HEAD}"
cached_ref="${CACHED_COMMIT_REF:-}"
branch="${BRANCH:-}"
production_branch="${NETLIFY_PRODUCTION_BRANCH:-main}"

echo "[netlify-ignore] branch=${branch:-unknown} production_branch=${production_branch}"

# Skip if nothing changed in the frontend base directory.
if [ -n "${cached_ref}" ]; then
  if git diff --quiet "${cached_ref}" "${current_ref}" -- .; then
    echo "[netlify-ignore] no frontend changes detected -> skipping build"
    exit 0
  fi
else
  echo "[netlify-ignore] missing CACHED_COMMIT_REF -> cannot diff, continuing checks"
fi

# Skip all non-production branches to avoid preview credit burn by default.
if [ "${branch}" != "${production_branch}" ]; then
  echo "[netlify-ignore] non-production branch (${branch}) -> skipping build"
  exit 0
fi

commit_message="$(git log -1 --pretty=%B "${current_ref}" 2>/dev/null || git log -1 --pretty=%B)"

# Allow build if we are on the production branch AND commit is a release
if [ "${branch}" == "${production_branch}" ]; then
  if echo "${commit_message}" | grep -qE '\[(release|deploy)\]'; then
    echo "[netlify-ignore] release commit detected -> allowing build"
    exit 1
  fi
  echo "[netlify-ignore] non-release commit on production branch -> skipping build"
  exit 0
fi

echo "[netlify-ignore] non-production branch -> skipping build"
exit 0
