# Milestone 32: Deployment Readiness & CSV Divergence Briefs

**Version:** 1.0.0
**Created:** 2026-02-19
**Status:** Completed and Archived
**Roadmap Items:** P1 Divergence Briefs (export), Netlify gate hardening, GitHub Releases (item #17), CHANGELOG update, Deployment Prep

---

## 1. Current State Summary

### What is done

| Area | Status |
|------|--------|
| **Divergence Briefs — JSON exports** | ✅ Complete. `computeMethodologyHomogeneity()` in `frontend/app/api/export/route.ts` injects a `methodology_homogeneity` block into JSON metadata for both raw and aggregated exports. Tests exist in `route.test.ts`. |
| **Divergence Briefs — analytics/trends** | ✅ Complete (M31). `queryMethodologyContext()` in `analytics/trends/route.ts` returns a `methodology_context` object with `divergence_note`, `is_homogeneous`, and per-group breakdowns. |
| **Divergence Briefs — compare endpoint** | ✅ Complete. `compare/route.ts` generates a human-readable `divergence_brief` string and a `comparable` boolean for two-hospital comparisons. |
| **Divergence Briefs — CSV exports** | ❌ Gap. CSV responses have no divergence signaling at all — no header comment, no extra column, no disclaimer row. |
| **Netlify release gate** | ⚠️ Bug. `frontend/scripts/netlify-ignore.sh` reaches the `production branch → exit 1 (allow build)` branch for every push to `main`, regardless of commit message. The `[release]` guard described in `GEMINI.md` is not enforced. |
| **GitHub Releases (item #17)** | ❌ Not started. No `release.yml` workflow. Tags exist locally but no GitHub Release objects with release notes are attached. |
| **Scraper scheduling** | ⚠️ Temporary cost-control mode active. `scraper-cron.yml` runs hourly (12:00–03:00 UTC) and bi-hourly (04:00–11:00 UTC). Target is `*/20` post-March-9 when Netlify billing resets. |
| **Production smoke** | ⚠️ `production-smoke.yml` requires `PRODUCTION_BASE_URL` secret; will fail until Netlify is unpaused. Intentionally offline — treat as warning only. |
| **CHANGELOG** | ⚠️ Last entry is v1.0.0 (2026-02-11). M19–M31 features are not reflected. |

### Key Unknowns / Assumptions

- **Assumption:** The Netlify project will be unpaused around March 9, 2026, by the user manually (not automatically). No automation exists to do this.
- **Assumption:** All four scrapers remain healthy until deployment. No scraper outage is anticipated but the `check_heartbeat` CLI should be re-run before tagging a release.
- **Unknown:** Whether the domain `wait-time.ca` DNS is fully pointed to Netlify yet. The roadmap says "cutover is staged in-repo but on hold." If DNS is not pointed, additional manual steps are needed.
- **Unknown:** Whether `NEXT_PUBLIC_BASE_URL` is correctly set in the Netlify environment (not in repo). This must be verified before re-enabling smoke tests.

---

## 2. Proposed Changes

This milestone has **three phases** and is scoped to 1–1.5 days of effort.

---

### Phase A — CSV Divergence Briefs (P1 Code Gap) [~3h]

**Goal:** Surface methodology divergence warnings in CSV exports so that researchers who download data are given the same scientific-validity context as JSON consumers.

**Design decision:** We will add an `X-Methodology-Divergence` HTTP response header to all CSV responses, and a `# METHODOLOGY WARNING: ...` comment row as the very first line of mixed-methodology CSVs. This is the lowest-friction, research-grade approach — it does not break CSV parsers that skip `#`-prefixed comment rows (pandas, Excel, R `read.csv`) and is self-documenting in the downloaded file.

#### [MODIFY] [route.ts](file:///home/jer/localsync/waittimecanada/frontend/app/api/export/route.ts)

- Extract `computeMethodologyHomogeneity(results)` call before both CSV branches (currently called only in JSON branches).
- For both the **raw CSV** and the **aggregated CSV** responses:
  - Prepend a `# METHODOLOGY DIVERGENCE WARNING: ...` comment line to the CSV body when `!is_homogeneous`.
  - Add response header `X-Methodology-Divergence: true|false`.
  - Add response header `X-Methodology-Groups: <N>` (number of distinct groups).
- No schema changes required.

#### [MODIFY] [route.test.ts](file:///home/jer/localsync/waittimecanada/frontend/app/api/export/route.test.ts)

Add four new test cases:
1. Mixed methodology → raw CSV contains `# METHODOLOGY DIVERGENCE WARNING` as first line.
2. Mixed methodology → raw CSV response has `X-Methodology-Divergence: true` header.
3. Homogeneous → raw CSV has no warning comment.
4. Aggregated CSV (granularity=daily) → divergence warning appears when mixed.

---

### Phase B — Netlify Release Gate Hardening (P1 Ops Gap) [~1h]

**Goal:** Enforce the intended `[release]` commit-message guard so that only explicitly tagged release commits trigger production Netlify deploys. This prevents accidental credit burn once Netlify is unpaused.

**Root cause:** In `netlify-ignore.sh`, the line `if [ "${branch}" == "${production_branch}" ]` is always true on `main`, so it always reaches `exit 1` (= allow build) before the commit message is ever checked. The `[release]` check (lines 31–34) is dead code.

#### [MODIFY] [netlify-ignore.sh](file:///home/jer/localsync/waittimecanada/frontend/scripts/netlify-ignore.sh)

Rewrite to implement the intended logic:
1. Skip if no frontend changes detected (existing diff check — keep this).
2. Skip all non-production branches (keep this).
3. On the production branch, **allow build only if commit message contains `[release]` or `[deploy]`**. Otherwise skip.

The corrected structure:
```bash
# After confirming we are on the production branch:
commit_message="$(git log -1 --pretty=%B "${current_ref}" 2>/dev/null || git log -1 --pretty=%B)"
if echo "${commit_message}" | grep -qE '\[(release|deploy)\]'; then
  echo "[netlify-ignore] release commit detected -> allowing build"
  exit 1
fi
echo "[netlify-ignore] non-release commit on production branch -> skipping build"
exit 0
```

**No test file exists** for this shell script. We will add a minimal sanity-check comment block at the top of the script explaining the exit-code contract (exit 0 = skip, exit 1 = build) as inline documentation.

---

### Phase C — GitHub Releases Automation (Item #17) [~2h]

**Goal:** Create a `release.yml` GitHub Actions workflow that auto-creates a GitHub Release with annotated release notes whenever a `v*.*.*` semver tag is pushed. This enables the `[1.0.0]` and future version changelogs to be visible on the GitHub Releases page.

#### [NEW] [release.yml](file:///home/jer/localsync/waittimecanada/.github/workflows/release.yml)

Workflow trigger: `push` to tags matching `v[0-9]+.[0-9]+.[0-9]+*`.

Steps:
1. Checkout repo.
2. Extract version from tag name (`GITHUB_REF_NAME`).
3. Extract the matching section from `CHANGELOG.md` using `awk` (everything between `## [VERSION]` and the next `## [`).
4. Use `actions/create-release@v1` (or the `softprops/action-gh-release@v2` action which is recommended and maintained) to publish a GitHub Release.
5. Set `draft: false`, `prerelease: false`.

The workflow will require the standard `GITHUB_TOKEN` (no additional secrets needed).

#### [MODIFY] [CHANGELOG.md](file:///home/jer/localsync/waittimecanada/CHANGELOG.md)

Add a `## [1.1.0] - 2026-02-19` section capturing M19–M31 features that were shipped after v1.0.0:
- M19: Governance & Quality (LICENSE, SECURITY.md, CODE_OF_CONDUCT, CITATION.cff, issue templates)
- M20: Reliability & Verification (API response time tracking, E2E pipeline, visual regression)
- M21: French Language Support (next-intl bilingual routing)
- M22: Portfolio Documentation (OpenAPI spec, MkDocs deployment)
- M23: Quality & Standardization (mypy strict, axe-core, mobile responsive tests, rate limiting)
- M25: Reliability & Verification Phase 2 (80% backend coverage, API integration tests)
- M26: Strategic Documentation (data dictionary, data flow architecture, property-based testing)
- M27: Operational Observability (drift monitor, /status page, Lighthouse CI, migration guide)
- M28: Ontario Real-Data Equity Layer (StatsCan CT overlays)
- M29: Equity Academic Rigor Hardening (uncertainty, non-causal messaging)
- M30: Scraper Visibility & Reliability Hardening (failure taxonomy, retry/backoff, enhanced health endpoints)
- M31: Divergence Briefs & Quality Drift UI (analytics + data-quality dashboard)
- Fix: Quebec parser zero-value guard (`ge=0`)
- Fix: Cache & polling audit (tight TTLs, `no-store` on user-specific routes)

Update `[Unreleased]` link at bottom.

---

## 3. Out of Scope for This Milestone

The following items from the roadmap are intentionally deferred and are **not** included here:

| Item | Reason Deferred |
|------|----------------|
| Netlify unpause / `wait-time.ca` cutover | Manual action by user; requires billing reset ~March 9, 2026 |
| `production-smoke` re-enablement | Blocked on Netlify coming back online |
| Scraper cron return to `*/20` | Blocked on billing reset |
| Enhanced equity layer (multi-province) | L-effort strategic item |
| Nova Scotia / New Brunswick scrapers | L-effort strategic item |
| Historical occupancy trends | L-effort strategic item |
| GitHub Project board (#47) | P2 overhead |
| Contributor onboarding guide (#40) | P2 docs |

---

## 4. Verification Plan

### A. CSV Divergence Briefs

**Automated — run existing + new tests:**
```bash
cd frontend
npm run test:unit -- --reporter=verbose route.test.ts
# Or target the specific file:
npx vitest run app/api/export/route.test.ts
```

New tests to add (per Phase A above) will verify:
- `# METHODOLOGY DIVERGENCE WARNING` present in CSV body when mixed.
- `X-Methodology-Divergence: true` header set.
- No warning when methodology is homogeneous.
- Aggregated granularity CSV also warns.

**Manual spot-check (after local `npm run dev`):**
1. Visit `http://localhost:3000/api/export?format=csv` — open the downloaded file, verify first line has no `#` warning (single-source homogeneous data).
2. If you have mixed-province data in the DB, filter to include both ON+QC: `?format=csv&province=` (no filter) — file should begin with `# METHODOLOGY DIVERGENCE WARNING`.
3. Check response headers via browser DevTools → Network → export request → `X-Methodology-Divergence` header visible.

### B. Netlify Release Gate

**Manual test — no automated test for shell script:**
1. Run `frontend/scripts/netlify-ignore.sh` locally with environment overrides:
   ```bash
   # Simulate non-release commit on main:
   BRANCH=main NETLIFY_PRODUCTION_BRANCH=main COMMIT_REF=HEAD \
     bash frontend/scripts/netlify-ignore.sh
   # Expected: exit 0 (skip)

   # Simulate [release] commit:
   # First, create a temp commit with that message or set COMMIT_REF to a commit with [release] in msg
   # Then:
   BRANCH=main NETLIFY_PRODUCTION_BRANCH=main COMMIT_REF=<release-commit-sha> \
     bash frontend/scripts/netlify-ignore.sh
   # Expected: exit 1 (allow)

   # Simulate non-main branch:
   BRANCH=feature/foo NETLIFY_PRODUCTION_BRANCH=main COMMIT_REF=HEAD \
     bash frontend/scripts/netlify-ignore.sh
   # Expected: exit 0 (skip)
   ```
2. Check exit code: `echo $?` after each run.

### C. GitHub Releases Workflow

**Manual test (dry-run approach):**
1. Validate the workflow YAML syntax:
   ```bash
   cd .github/workflows
   # If you have the GitHub CLI installed:
   gh workflow view release.yml
   # Or simply YAML-lint it:
   python3 -c "import yaml; yaml.safe_load(open('release.yml'))" && echo "Valid YAML"
   ```
2. After merging, tag a release:
   ```bash
   git tag v1.1.0 -a -m "Release v1.1.0"
   git push origin v1.1.0
   ```
3. Verify the GitHub Actions tab shows `Release` workflow running.
4. Verify the Releases page on GitHub shows the new release with extracted CHANGELOG notes.

**CHANGELOG sanity check:**
```bash
grep -c "## \[" CHANGELOG.md   # Should return 5 (Unreleased, 1.1.0, 1.0.0, 0.9.0, 0.8.0, 0.1.0)
```

---

## 5. Timeline & Milestones

| Date | Milestone |
|------|-----------|
| **Feb 20–21** | Implement Phase A (CSV divergence), write + pass tests |
| **Feb 21** | Implement Phase B (netlify-ignore.sh fix) |
| **Feb 22** | Implement Phase C (release.yml, CHANGELOG update) |
| **Feb 22** | Full test suite run (`npm run test:unit`, `pytest tests/unit`), confirm passing |
| **Feb 22** | Commit with message `feat: M32 CSV divergence briefs, Netlify gate hardening, GitHub Releases` |
| **~Mar 9** | (Post-billing-reset) Manually unpause Netlify, push `[release]` commit, verify smoke |

**Effort estimate:** ~6-7 hours total (spread across 2-3 days).

---

## 6. Rollback Approach

| Change | Rollback |
|--------|---------|
| CSV divergence headers/comment | Revert `route.ts` changes; the JSON behavior is unchanged and tests will gate regression |
| `netlify-ignore.sh` | Revert to current version; cost impact is the same (Netlify is paused anyway) |
| `release.yml` | Delete the file; no releases will be created until re-added |
| CHANGELOG | Revert CHANGELOG entries; git history is the ground truth |

All changes are additive or configuration-only. No database migrations required.

---

## 7. Dependency Summary

```
Phase A (CSV divergence) → No external deps; modifies frontend only
Phase B (Netlify gate)   → No external deps; modifies shell script only
Phase C (GitHub Releases)→ Depends on CHANGELOG being updated (Phase C includes this)
                           Uses softprops/action-gh-release@v2 (pinned to SHA for security)
Deployment (post-March 9)→ Manual user action on Netlify dashboard
```

---

## 8. Open Questions (Non-Blocking)

1. **CSV warning format:** The plan uses a `#`-prefixed comment row as the first line. An alternative is to append a separate `_divergence_warnings.txt` sidecar in a ZIP archive. The comment-row approach is simpler and more research-friendly. Proceed unless you prefer the ZIP approach.

2. **Release tagging convention:** The plan assumes `v1.1.0` for the next release. Given that M28/M29 added substantial capability (real StatsCan equity data), a bump to `v2.0.0` is equally defensible. Proceeding with `v1.1.0` unless you prefer a major bump.

3. **`netlify-ignore.sh` — `[deploy]` alias:** The plan allows both `[release]` and `[deploy]` in commit message to trigger a build, consistent with the mention in `scripts/verify-production-ops.sh`. Let me know if you want only `[release]`.
