# Milestone 31 — Divergence Briefs & Quality Drift UI
**Version:** v1.0 | **Date:** 2026-02-19 | **Status:** Draft — Awaiting Review

---

## Current State Summary

After a full codebase review, the following is confirmed:

### What already exists (do not re-implement)

| Layer | Capability | Location |
|-------|-----------|----------|
| **Backend** | `are_comparable()` + `generate_divergence_brief()` (canonical Python logic) | `backend/src/waittime/core/models.py` |
| **Backend** | `ComparisonService.compare_hospitals()` — pairwise divergence briefs | `backend/src/waittime/services/comparison.py` |
| **Backend** | `QualityDiffService.get_source_diff()` + `get_source_trend()` — snapshot diffs | `backend/src/waittime/services/quality_diff.py` |
| **Frontend API** | `/api/compare` — pairwise divergence brief per request | `frontend/app/api/compare/route.ts` |
| **Frontend API** | `/api/data-quality?view=diff&source_id=...` — per-source quality diff | `frontend/app/api/data-quality/route.ts` |
| **Frontend API** | `/api/export` — `methodology_homogeneity` + `divergence_note` in JSON metadata | `frontend/app/api/export/route.ts` |
| **Tests** | `test_quality_diff.py` — 5 unit tests for `QualityDiffService` | `backend/tests/unit/test_quality_diff.py` |
| **Tests** | `test_comparison_service.py` — pairwise comparison service coverage | `backend/tests/unit/test_comparison_service.py` |

### Key gaps (what this milestone actually builds)

1. **Analytics/trends API route lacks methodology context.** The `/api/analytics/trends` route aggregates cross-province data but emits no indicator of how many distinct methodology groups are mixed into the trend — researchers have no signal that the numbers may not be scientifically comparable.

2. **No frontend UI for quality drift.** Although `/api/data-quality?view=diff` is fully functional, the `/data-quality` page never calls it. There are no diff delta panels showing per-source degradation/improvement trends to operators.

3. **No automated snapshot scheduling.** The `snapshot_daily_quality` function in `DataQualityService` exists but is not called on any schedule (no cron job, no CLI entry point). Without daily snapshots, the `view=diff` API has nothing to diff against.

### Key unknowns / assumptions

- Assumes `data_quality_snapshots` is being populated in production (at least partially) via the existing `snapshot_daily_quality` path. If it is not, Phase C must ship before Phase B has any visible data. **This should be verified before execution.**
- The analytics trends route currently pulls from `measurement_aggregates`, which are already populated by the aggregation pipeline. No DB migration needed.
- No breaking API contract changes. All new fields are additive.
- Production deployment is blocked until ~March 9, 2026 (Netlify unpause). All work is local/CI-verifiable.

---

## Proposed Changes

This milestone is three independent phases that can be implemented & verified sequentially. They share no hard dependencies between them, but Phase B depends on Phase C for *real* data to appear in the UI.

---

### Phase A — Methodology Divergence Context in Analytics Trends API

**Goal:** Annotate the `/api/analytics/trends` response with methodology group metadata so the UI (and researchers downloading the JSON) know whether the trend mixes methodologies.

**Deliverables:**
- Add `methodology_context` block to the `/api/analytics/trends` response.
- Add an optional `?province=ALL` aggregate-across-province mode that explicitly flags cross-province methodology divergence.
- Update the analytics trends test to assert the new field is present.

#### [MODIFY] [analytics trends route.ts](file:///home/jer/localsync/waittimecanada/frontend/app/api/analytics/trends/route.ts)

Add a SQL query pass that fetches distinct `(metric_family, start_event, end_event, statistic_type)` groups for the hospitals in the selected province+lookback window, then compute:

```ts
methodology_context: {
  distinct_groups: number;           // 1 = homogeneous, >1 = divergent
  is_homogeneous: boolean;
  divergence_note: string | null;    // null if homogeneous
  groups: Array<{
    metric_family: string;
    start_event: string;
    end_event: string;
    statistic_type: string;
    hospital_count: number;
  }>;
}
```

This is purely additive — existing consumers of the API are unaffected.

#### [MODIFY] [analytics-trends.test.ts](file:///home/jer/localsync/waittimecanada/frontend/tests/api/analytics-trends.test.ts)

Add one new assertion: the `GET /api/analytics/trends?province=ON&period=monthly&lookback=6m` response body contains `data.methodology_context` with at least `is_homogeneous` and `distinct_groups`.

---

### Phase B — Quality Drift Panel on /data-quality Page

**Goal:** Surface the per-source quality diff data that is already available at `/api/data-quality?view=diff&source_id=<id>` in a visible UI panel on the `/data-quality` page.

**Deliverables:**
- New `QualityDriftPanel` React component that calls the diff API for all 4 sources (ON, QC, AB, BC).
- Displays: success rate delta, hospitals reporting delta, worst-gap delta, and the human-readable summary string.
- Color-coded status indicators: green/stable/red based on `success_rate_delta`.
- Integrated into `/data-quality` page below the current per-source health table.
- Unit tests for the new component.

#### [NEW] [QualityDriftPanel.tsx](file:///home/jer/localsync/waittimecanada/frontend/components/QualityDriftPanel.tsx)

```tsx
// Fetches /api/data-quality?view=diff&source_id={id}&compare_days=7 for each source
// Renders a card per source: summary sentence + 3 delta chips
// Skeleton loading state while fetching
// Handles has_baseline=false gracefully ("No baseline data yet")
```

#### [MODIFY] [data-quality page.tsx](file:///home/jer/localsync/waittimecanada/frontend/app/[locale]/data-quality/page.tsx)

Import and render `<QualityDriftPanel />` below the existing scraper health table, inside a "7-Day Quality Drift" section heading.

#### [NEW] [QualityDriftPanel.test.tsx](file:///home/jer/localsync/waittimecanada/frontend/tests/components/QualityDriftPanel.test.tsx)

Three test cases using `vi.fn()` mock for `fetch`:
1. Renders delta chips when `has_baseline: true` and `success_rate_delta` is negative (degraded) → red chip.
2. Renders "No baseline data" fallback when `has_baseline: false`.
3. Renders skeleton loading state before fetch resolves.

---

### Phase C — Daily Snapshot Population (CLI + Cron)

**Goal:** Ensure `data_quality_snapshots` is populated daily so Phase B has real data to display. This is the lowest-risk infrastructure change.

**Deliverables:**
- New CLI entry point: `python -m waittime.cli.snapshot_quality [--date YYYY-MM-DD] [--backfill-days N]`
- GitHub Actions cron job that calls the snapshot CLI once daily (01:00 UTC) after scrapers have run.
- Backfill invocation for the last 30 days to seed initial data.

#### [NEW] [snapshot_quality CLI](file:///home/jer/localsync/waittimecanada/backend/src/waittime/cli/snapshot_quality.py)

Thin wrapper around `DataQualityService.snapshot_daily_quality()`. Accepts:
- `--date YYYY-MM-DD` (defaults to yesterday)
- `--backfill-days N` (runs snapshot for today minus N through today, idempotent)

```python
# Usage examples:
# python -m waittime.cli.snapshot_quality                 # snapshot yesterday
# python -m waittime.cli.snapshot_quality --date 2026-02-18
# python -m waittime.cli.snapshot_quality --backfill-days 30
```

#### [MODIFY] [pyproject.toml](file:///home/jer/localsync/waittimecanada/backend/pyproject.toml)

Add `snapshot_quality = "waittime.cli.snapshot_quality:main"` to `[project.scripts]`.

#### [NEW] [snapshot-cron.yml](file:///home/jer/localsync/waittimecanada/.github/workflows/snapshot-cron.yml)

```yaml
# Runs daily at 01:00 UTC, after scrapers have had a chance to collect data
on:
  schedule:
    - cron: '0 1 * * *'
  workflow_dispatch:    # allows manual trigger
jobs:
  snapshot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -e 'backend/.[dev]'
      - run: python -m waittime.cli.snapshot_quality
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

#### [NEW] [test_snapshot_quality_cli.py](file:///home/jer/localsync/waittimecanada/backend/tests/unit/test_snapshot_quality_cli.py)

Unit tests verifying:
1. Default date is yesterday UTC.
2. `--date` flag parses correctly and calls `snapshot_daily_quality` with that date.
3. `--backfill-days 3` calls the service 3 times (one per day), idempotently.
4. Graceful exit (no exception) when DB returns zero hospitals.

---

## Verification Plan

### Automated Tests

**Backend — run from `backend/` with venv active:**

```bash
# Run all existing + new unit tests (should pass as-is; new tests added in Phase C)
pytest tests/unit/ -v --tb=short

# Run just the new snapshot CLI tests
pytest tests/unit/test_snapshot_quality_cli.py -v

# Run full suite with coverage (target: stays >=80%)
pytest tests/ -v --cov=waittime --cov-report=term-missing
```

**Frontend — run from `frontend/`:**

```bash
# Run all unit tests (should continue to pass)
npm run test:unit

# Run just the new tests
npx vitest run tests/api/analytics-trends.test.ts
npx vitest run tests/components/QualityDriftPanel.test.tsx

# Type check (must pass with zero errors)
npm run type-check

# Lint
npm run lint
```

### Manual Verification

After running `python -m waittime.cli.snapshot_quality --backfill-days 7` with the real `DATABASE_URL`:
1. Query `SELECT COUNT(*) FROM data_quality_snapshots WHERE snapshot_date >= CURRENT_DATE - 7;` — expect a non-zero row count.
2. Open `http://localhost:3000/data-quality` (with `npm run dev`) — a "7-Day Quality Drift" section should appear below the scraper health table with per-source cards.
3. Curl the trends API and verify the new field: `curl "http://localhost:3000/api/analytics/trends?province=ON&period=monthly&lookback=6m" | jq '.data.methodology_context'` — expect `is_homogeneous: true` for ON (all hospitals use the same Ontario Health methodology).

---

## Timeline & Milestones

| Phase | Estimated Effort | Sequence |
|-------|-----------------|---------|
| **Phase C** — Snapshot CLI + cron | ~3h | First (generates baseline data) |
| **Phase A** — Analytics methodology context field | ~3h | Second (purely additive API change) |
| **Phase B** — QualityDriftPanel UI + tests | ~5h | Third (depends on snapshot data) |
| **Docs + roadmap update** | ~1h | Final |
| **Total** | ~12h | — |

**Target complete:** Within the "Now (0-2 weeks)" window. All work is local+CI; no production deployment needed.

---

## Rollout / Rollback

- **All API changes are additive.** No existing response contract is altered. Rollback = revert the relevant commit; no DB migration to reverse.
- **Snapshot cron** is safe to enable: the underlying `snapshot_daily_quality` call is idempotent (skips already-snapshotted dates). Disabling the workflow is trivially `workflow_dispatch: …` set to paused or the file deleted.
- **UI panel** degrades gracefully: if `has_baseline: false`, the component renders a visible "No baseline data yet" message rather than breaking.
- **No DB migrations** required for this milestone.

---

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| `data_quality_snapshots` table is empty in production | Medium | Phase C ships first with a backfill flag; UI handles the empty-baseline case gracefully |
| Analytics trends route SQL for methodology groups is slow | Low | Query is on `measurement_aggregates` (indexed, small table); add `EXPLAIN` check if needed |
| Cron adds GitHub Actions minutes | Low | One lightweight Python job/day is ~30 seconds; well within free tier |
| Netlify deploy blocked until March 9 | Confirmed | No frontend verification against production needed; local dev server sufficient |
