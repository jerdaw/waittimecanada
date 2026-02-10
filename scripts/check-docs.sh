#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

failures=0

echo "Running docs quality checks..."

check_paths=(
  "README.md"
  "CONTRIBUTING.md"
  "backend/README.md"
  "backend/docs"
  "frontend/README.md"
  "docs/README.md"
  "docs/API.md"
  "docs/adr"
  "docs/getting-started"
  "docs/architecture"
  "docs/development"
  "docs/planning/README.md"
  "docs/planning/manual-tasks.md"
  "docs/planning/roadmap-process.md"
  "docs/planning/roadmap.md"
  ".github/workflows/README.md"
)

mapfile -t all_md_files < <(
  find "${check_paths[@]}" -type f -name "*.md" 2>/dev/null | sort
)

exclude_files=(
  "docs/adr/template.md"
  "docs/REPO_STRUCTURE_PLAN.md"
  "docs/final-documentation-review.md"
  "docs/planning/strategic-plan.md"
  "docs/planning/expansion-roadmap.md"
  "docs/planning/competitor-design-analysis.md"
  "docs/planning/scraper-status-2026-02-04.md"
  "docs/planning/ux-seo-implementation-plan.md"
)

md_files=()
for file in "${all_md_files[@]}"; do
  skip_file=0
  for excluded in "${exclude_files[@]}"; do
    if [[ "${file}" == "${excluded}" ]]; then
      skip_file=1
      break
    fi
  done

  if [[ "${skip_file}" -eq 0 ]]; then
    md_files+=("${file}")
  fi
done

if [[ ${#md_files[@]} -eq 0 ]]; then
  echo "No markdown files found for checks."
  exit 1
fi

echo
echo "[1/3] Checking for absolute file:// links..."
if rg -n "\\]\\(file://" "${md_files[@]}"; then
  failures=1
else
  echo "OK: no file:// links found."
fi

echo
echo "[2/3] Checking for non-human co-author trailers..."
mapfile -t text_files < <(git ls-files "*.md" "*.txt" "*.rst")
if rg -n -i "^Co-Authored-By:\\s*.*(claude|codex|gemini|chatgpt|ai assistant|automated tool)" "${text_files[@]}"; then
  failures=1
else
  echo "OK: no non-human co-author trailers found."
fi

echo
echo "[3/4] Checking repository-relative markdown links..."
while IFS= read -r file; do
  file_dir="$(dirname "${file}")"

  while IFS= read -r raw_link; do
    link="${raw_link%% *}"
    link="${link%%#*}"
    link="${link%%\\?*}"

    if [[ -z "${link}" ]]; then
      continue
    fi

    if [[ "${link}" =~ ^(https?://|mailto:|#) ]]; then
      continue
    fi

    if [[ "${link}" == "<"*">" ]]; then
      link="${link#<}"
      link="${link%>}"
    fi

    if [[ "${link}" =~ ^[a-zA-Z]+: ]]; then
      continue
    fi

    if [[ "${link}" == /* ]]; then
      target="${ROOT_DIR}${link}"
    else
      target="${ROOT_DIR}/${file_dir}/${link}"
    fi

    if [[ ! -e "${target}" ]]; then
      echo "Broken link target in ${file}: ${raw_link}"
      failures=1
    fi
  done < <(perl -nE 'while(/\[[^\]]+\]\(([^)]+)\)/g){ say $1 }' "${file}")
done < <(printf "%s\n" "${md_files[@]}")

echo
echo "[4/4] Checking roadmap consistency..."
if python3 backend/scripts/verify_roadmap_consistency.py; then
  echo "OK: roadmap consistency checks passed."
else
  echo "Roadmap consistency check failed."
  failures=1
fi

if [[ "${failures}" -ne 0 ]]; then
  echo
  echo "Docs quality checks failed."
  exit 1
fi

echo
echo "Docs quality checks passed."
