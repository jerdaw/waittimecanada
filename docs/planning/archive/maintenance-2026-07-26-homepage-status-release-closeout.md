# Homepage Coverage and Status Semantics Release Closeout

**Status:** Closed

**Date:** 2026-07-26

**Application release:** `744fd5c6c86bc81db0023c928383f080fd152a41`

## Scope

Close out repository maintenance for the exact homepage coverage and public
status-semantics correction. Private deployment paths, credentials, monitoring
configuration, and environment-specific operator procedures remain outside
this public repository.

## Completed Behavior

- `/api/hospitals` returns a database-derived national `coverage` snapshot
  alongside the filtered or paginated top-level `count`.
- The homepage server-renders the exact national hospital and province counts,
  seeds the client with that snapshot, and refreshes coverage at the existing
  low-frequency visibility-aware interval.
- Province-filtered hospital counts remain distinct from national coverage.
- Approximate `...+ Hospitals` copy and the obsolete four-hour cadence claim
  are absent from server-rendered and hydrated homepage states.
- `/api/status` declares that `overall_status` is based on distinct UTC
  measurement-hour completeness over 24 hours.
- `/api/health` remains the current source-freshness signal and exposes the
  active stale threshold.

## Root-Cause Conclusion

The observed combination of healthy current sources and
`overall_status=critical` with `system_uptime_24h=0.458` was coherent. The
freshness endpoint showed recent successful source heartbeats within the
120-minute threshold, while the status endpoint represented 11 distinct
measurement hours out of 24. Delayed or skipped scheduled starts reduced
24-hour completeness even after a recent successful run restored freshness.

## Regression Coverage

- Hospital API tests cover the national coverage envelope and filtered-count
  distinction.
- Homepage tests cover server-rendered coverage and hydration seeding.
- Hero and message tests cover exact count and hourly-source-check copy.
- Status route and page tests cover the explicit completeness basis and UTC
  window.
- Production smoke validates exact public coverage and rejects approximate or
  obsolete cadence copy.
- Browser E2E coverage remains CI-first under
  `docs/development/testing-guidelines.md`; no routine local Playwright run is
  required for this maintenance closeout.

## Release Evidence

- Pull request: <https://github.com/jerdaw/waittimecanada/pull/93>
- Production smoke:
  <https://github.com/jerdaw/waittimecanada/actions/runs/30054639138>
- The smoke workflow completed successfully at `2026-07-23T23:55:40Z`
  against the application release above.
- The dated public HTML/API snapshot reported 4 provinces and 399 hospitals,
  exact non-approximate homepage coverage, HTTP 200 responses from
  `/api/health` and `/api/status`, and no obsolete cadence copy.

## Maintenance Verification

- Documentation quality checks and strict MkDocs build passed.
- Roadmap consistency validation and 52 focused backend documentation tests
  passed.
- Frontend lint, production TypeScript checking, and production build passed.
- The 28 focused homepage, hospital coverage, cadence, status-route, and
  status-page tests passed.
- The test-file TypeScript check retains older Vitest mock-generic errors in
  `TemporalPatterns.test.tsx`, `analytics.test.tsx`, and
  `server-cache.test.ts`; this maintenance does not mask or expand into that
  unrelated typing debt.
- Local Playwright was not run, as required by the CI-first browser-test policy.

## Remaining Follow-Ups

No new repository implementation task is opened by this closeout. The roadmap
continues to track the external scheduler/offload proof and cadence acceptance
work. Current freshness and recent completeness should continue to be reviewed
together when evaluating scheduler reliability.
