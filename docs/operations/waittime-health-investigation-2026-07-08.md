# WaitTime Health Investigation - 2026-07-08

## Executive Summary

Production health was critical because:

1. The scraper and heartbeat workflows had their scheduled triggers paused and were `workflow_dispatch` only.
2. Production scraper data had not been refreshed since June 4, 2026, leaving all source heartbeat ages far outside the public freshness threshold.
3. A manual scraper run from the old remote code would hit the current Ontario redirect chain unless the Ontario scraper followed redirects.

Recovery status after the 2026-07-08 fix:

- Scraper source behavior: all four sources collect current data locally and in the production scraper workflow after the Ontario redirect fix.
- Production database freshness: `/api/health` is healthy with all four source heartbeats refreshed at `2026-07-09T10:48Z` by a freshness-only manual recovery run.
- Recurrence configuration: `scraper-cron.yml` is restored to hourly schedule plus manual dispatch; `heartbeat-monitor.yml` is restored to a 30-minute schedule plus manual dispatch. On 2026-07-08, the schedules were staggered away from common `:00` and `:30` GitHub Actions boundaries. On 2026-07-09, heartbeat gained an automatic freshness-only scraper recovery dispatch when its heartbeat check fails and no scraper run is already queued or running.
- Recurrence verification: GitHub Actions created successful post-recovery `event=schedule` runs for both heartbeat and scraper. The first observed heartbeat scheduled run was `28987119740` at `2026-07-09T01:15Z`; the first observed scraper scheduled run was `28994059457` at `2026-07-09T04:27Z`. Later observation showed scraper schedule creation was still intermittent enough to breach the 120-minute freshness threshold, so heartbeat recovery dispatch was added as a second GitHub-hosted guard.
- Scraper workflow timeout mitigation: the scraper workflow now records source-health summary and freshness badge evidence before analytics aggregation, gives the job a 35-minute budget, bounds the aggregate step to 15 minutes, limits routine post-scrape aggregate refresh to the daily bucket, and exposes `refresh_analytics=false` for emergency manual freshness refreshes. The first post-mitigation scheduled run completed successfully, including aggregate refresh.
- Residual public status: `/api/status` and `/api/data-quality` still report `critical` because their 24-hour uptime calculation expects 24 hourly windows. They should recover as successful hourly runs accumulate.

## Root-Cause Table

| Finding | Evidence | Current or stale | Severity | Follow-up |
| --- | --- | --- | --- | --- |
| Scheduled scraper paused | Local and remote workflow YAML showed `workflow_dispatch` only; latest scraper run before recovery was `2026-06-04T23:32:34Z` | fixed | high | hourly schedule restored in `6ad2fa2`; manual dispatch remains available |
| Heartbeat monitor paused | Local and remote workflow YAML showed `workflow_dispatch` only; latest heartbeat run before recovery was `2026-06-04T23:55:21Z` | fixed | high | 30-minute schedule restored in `6ad2fa2`; manual dispatch run `28976114340` passed |
| Heartbeat scheduled event creation after restore | Heartbeat monitor produced successful scheduled run `28987119740` at `2026-07-09T01:15:21Z` | fixed | high | keep observing normal heartbeat cadence |
| Scraper scheduled event creation after restore | Scraper workflow produced successful scheduled runs `28994059457` at `2026-07-09T04:27:35Z` and `29003323296` at `2026-07-09T08:00:40Z`, but no later run arrived before `/api/health` became stale at `2026-07-09T10:41Z` | mitigated | high | heartbeat workflow now dispatches a freshness-only scraper recovery when its stale check fails; continue ADR-0027 trusted-runner offload work |
| Heartbeat-triggered scraper recovery | Heartbeat runs every 30 minutes and now has `actions: write`, a guarded stale-check failure condition, active/queued scraper-run checks, and `refresh_analytics=false` dispatch | new mitigation | high | observe the first natural stale-heartbeat recovery event; manual dispatch remains available |
| Post-scrape aggregate timeout | Manual scraper run `28990136047` completed scraper writes, but the workflow was cancelled when `Refresh current analytics aggregates` exceeded the 20-minute job timeout; post-mitigation scheduled run `28994059457` completed in 11m29s | fixed | medium | keep daily-only aggregate guardrail and emergency `refresh_analytics=false` fallback |
| Ontario redirect handling | Old source URL redirects through Ontario Health before returning 200; original fetch path did not follow redirects | fixed | high | redirect-following fix merged in `3a3f63b` and used by production scraper run `28975214976` |
| Quebec 403 | Production last error is from `2026-06-04T23:33:38.599Z`; current endpoint probe returns 200 and local dry-run collects data | stale | medium | no scraper fix needed unless production run reproduces |
| DB source URL metadata | Migration runner rejects checksum changes to applied migrations; source URL update requires a new migration | fixed | medium | migration workflow run `28975179871` applied `022_update_ontario_health_source_url.sql` |

## Operator Commands

Use these only after the fix and migration are committed and pushed to the ref used by the workflow:

```powershell
gh workflow run database-migrate.yml --repo jerdaw/waittimecanada --ref main
gh run watch <migration-run-id> --repo jerdaw/waittimecanada --exit-status

gh workflow run scraper-cron.yml --repo jerdaw/waittimecanada --ref main
gh run watch <scraper-run-id> --repo jerdaw/waittimecanada --exit-status

# Emergency freshness-only fallback if aggregate refresh is suspected slow:
gh workflow run scraper-cron.yml --repo jerdaw/waittimecanada --ref main -f refresh_analytics=false
gh run watch <scraper-run-id> --repo jerdaw/waittimecanada --exit-status

Invoke-RestMethod -Uri 'https://wait-time.ca/api/health' -TimeoutSec 20
Invoke-RestMethod -Uri 'https://wait-time.ca/api/status' -TimeoutSec 20
```

## Recovery Evidence

Captured at: 2026-07-09T10:50Z

| Item | Evidence | Result |
| --- | --- | --- |
| Redirect/source fix | Commit `3a3f63b` | Ontario scraper follows redirects and source metadata points to the current Ontario Health URL |
| Investigation record | Commit `c0e229d` | Baseline, dry-run, migration, and production action evidence recorded |
| Recurrence fix | Commits `6ad2fa2` and `a662a55` | Scraper schedule restored to hourly at minute 29; heartbeat schedule restored to minutes 14 and 44 |
| Scraper workflow hardening | Commit `d54764d` | Freshness summary and badge run before daily aggregate refresh; workflow has a 35-minute job timeout, 15-minute aggregate step timeout, and `refresh_analytics=false` manual fallback |
| Heartbeat recovery hardening | Current workflow change | Heartbeat can dispatch `scraper-cron.yml` with `refresh_analytics=false` after a failed stale-heartbeat check, unless a scraper run is already queued or running |
| Workflow state | GitHub API check at `2026-07-08T23:31:54Z` | `scraper-cron.yml` and `heartbeat-monitor.yml` both reported `active` after an explicit off/on toggle |
| Migration workflow | Run `28975179871`, <https://github.com/jerdaw/waittimecanada/actions/runs/28975179871> | success |
| Production scraper workflow | Run `28975214976`, <https://github.com/jerdaw/waittimecanada/actions/runs/28975214976> | success; 403 did not recur; all four source heartbeats refreshed |
| Manual fallback scraper workflow | Run `28981235847`, <https://github.com/jerdaw/waittimecanada/actions/runs/28981235847> | success; refreshed production at `2026-07-08T22:52:40.371Z` |
| Manual threshold-protection scraper workflow | Run `28985629245`, <https://github.com/jerdaw/waittimecanada/actions/runs/28985629245> | success; refreshed production at `2026-07-09T00:37:35.818Z` before the 120-minute freshness threshold was breached |
| Manual scraper fallback with aggregate timeout | Run `28990136047`, <https://github.com/jerdaw/waittimecanada/actions/runs/28990136047> | scraper step succeeded and refreshed production at `2026-07-09T02:39:47.923Z`; workflow later cancelled in aggregate refresh at the 20-minute job timeout |
| Manual freshness-only fallback after hardening | Run `28991123636`, <https://github.com/jerdaw/waittimecanada/actions/runs/28991123636> | success on commit `d54764d`; completed in 1m58s with `refresh_analytics=false`, proving emergency freshness-only dispatch |
| Scheduled scraper after hardening | Run `28994059457`, <https://github.com/jerdaw/waittimecanada/actions/runs/28994059457> | success on commit `d54764d`; first observed post-recovery scraper `event=schedule`; completed in 11m29s including daily aggregate refresh |
| Scheduled scraper on final evidence commit | Run `29003323296`, <https://github.com/jerdaw/waittimecanada/actions/runs/29003323296> | success on commit `ccd6d76`; production refreshed at `2026-07-09T08:01:56.493Z` |
| Intermittent schedule freshness breach | `/api/health` check at `2026-07-09T10:41Z` | unhealthy; latest update `2026-07-09T08:01:56.493Z`; source ages about 160 minutes against the 120-minute threshold |
| Manual freshness-only recovery after freshness breach | Run `29012487518`, <https://github.com/jerdaw/waittimecanada/actions/runs/29012487518> | success on commit `ccd6d76`; completed in 1m45s, skipped aggregate refresh, and refreshed production at `2026-07-09T10:48:45.915Z` |
| Heartbeat workflow | Run `28976114340`, <https://github.com/jerdaw/waittimecanada/actions/runs/28976114340> | success on restored workflow definition |
| Manual fallback heartbeat workflow | Run `28981626628`, <https://github.com/jerdaw/waittimecanada/actions/runs/28981626628> | success on commit `a662a55` |
| Manual final heartbeat fallback | Run `28986301737`, <https://github.com/jerdaw/waittimecanada/actions/runs/28986301737> | success after the latest manual scraper refresh |
| Scheduled heartbeat | Run `28987119740`, <https://github.com/jerdaw/waittimecanada/actions/runs/28987119740> | success; first observed post-recovery `event=schedule` run |
| Production smoke workflow | Run `28976114348`, <https://github.com/jerdaw/waittimecanada/actions/runs/28976114348> | success against `https://wait-time.ca` |
| Local production smoke | `PRODUCTION_BASE_URL=https://wait-time.ca bash scripts/production-smoke.sh` at `2026-07-09T10:41Z` | passed all public route/API checks and found no dormant legacy source IDs |
| Docs CI | Run `28976106659`, <https://github.com/jerdaw/waittimecanada/actions/runs/28976106659> | success after recurrence docs update |
| Workflow guardrail check | `python3 scripts/check-scraper-workflow.py` | passes after mitigation; fails if scraper freshness evidence is placed after aggregate refresh, aggregate refresh lacks its own timeout, emergency aggregate skip is removed, or heartbeat recovery dispatch guardrails are removed |

### Scheduled-Event Observation

| Workflow | Expected UTC slot | Observation |
| --- | --- | --- |
| `heartbeat-monitor.yml` | `2026-07-08T23:14Z` | no new `event=schedule` run by `2026-07-08T23:23Z` |
| `scraper-cron.yml` | `2026-07-08T23:29Z` | no new `event=schedule` run by `2026-07-08T23:31Z` |
| `heartbeat-monitor.yml` | `2026-07-08T23:44Z` | no new `event=schedule` run by `2026-07-08T23:48Z` |
| `heartbeat-monitor.yml` | `2026-07-09T00:14Z` | no new `event=schedule` run by `2026-07-09T00:21Z` |
| `scraper-cron.yml` | `2026-07-09T00:29Z` | no new `event=schedule` run by `2026-07-09T00:36Z`; manual fallback dispatched |
| `heartbeat-monitor.yml` | `2026-07-09T00:44Z` | no new `event=schedule` run by `2026-07-09T00:51Z` |
| `heartbeat-monitor.yml` | `2026-07-09T01:14Z` | successful `event=schedule` run created at `2026-07-09T01:15:21Z` |
| `scraper-cron.yml` | `2026-07-09T01:29Z` | no new `event=schedule` run observed by the `2026-07-09T02:37Z` check |
| `scraper-cron.yml` | `2026-07-09T02:29Z` | no new `event=schedule` run observed by the `2026-07-09T02:37Z` check; manual fallback dispatched |
| `scraper-cron.yml` | `2026-07-09T03:29Z` | no new `event=schedule` run observed by the `2026-07-09T03:38Z` check |
| `scraper-cron.yml` | `2026-07-09T04:29Z` | successful `event=schedule` run created at `2026-07-09T04:27:35Z`; production refreshed at `2026-07-09T04:34:00.400Z` |
| `scraper-cron.yml` | `2026-07-09T08:00Z` | successful `event=schedule` run created at `2026-07-09T08:00:40Z`; production refreshed at `2026-07-09T08:01:56.493Z` |
| `scraper-cron.yml` | `2026-07-09T10:41Z` | no newer scraper run had arrived before the freshness threshold was breached; manual freshness-only fallback dispatched |

Latest post-refresh API state:

| Endpoint | Observed status | Key evidence | Interpretation |
| --- | --- | --- | --- |
| `/api/health` | 200, healthy | `last_update=2026-07-09T10:48:45.915Z`; source ages about 1 minute at the `2026-07-09T10:49Z` check; source counts: AB 22, BC 7, ON 166, QC 183 | current scraper freshness recovered from a freshness-only manual run after an intermittent schedule gap |
| `/api/status` | 200, critical | `system_uptime_24h=0.292`; `scheduler_cadence=hourly`; `expected_runs_24h=24`; all source heartbeats healthy after recovery | current freshness is healthy, but the 24-hour success-rate window is still recovering from the long gap and missed schedule windows |
| `/api/data-quality` | 200, critical | `system_uptime_24h=0.292`; `total_measurements_24h=2774`; all source heartbeats healthy after recovery | measurements are flowing again, but the 24-hour data-quality success-rate window needs sustained recurring runs to recover |

## Baseline

- Captured at: 2026-07-08T20:49:03Z
- Operator: Jeremy Dawson
- Public base URL: https://wait-time.ca

## Public API Evidence

| Endpoint | Observed status | Key evidence | Interpretation |
| --- | --- | --- | --- |
| `/api/health` | 200, unhealthy | `last_update=2026-06-04T23:33:38.599Z`; `stale_threshold_minutes=120`; sources: `alberta-ahs:stale:48796m`, `bc-phsa:stale:48796m`, `ontario-health:stale:48796m`, `quebec-msss:error:48795m` | scraper freshness failure; all source heartbeats are far outside the public threshold |
| `/api/status` | 200, critical | `generated_at=2026-07-08T20:49:06.533Z`; `scheduler_cadence=hourly`; `expected_runs_24h=24`; `system_uptime_24h=0`; all source heartbeat ages about 48,796 minutes | production status reflects stale scraper heartbeats, not a down frontend/API |
| `/api/data-quality` | 200, critical | `overall_status=critical`; all four sources report `measurements_24h=0`, `last_24h_success_rate=0`, and heartbeat ages about 48,796 minutes | data-quality critical state is consistent with no recent scraper writes |

Quebec production state at baseline:

| Field | Value |
| --- | --- |
| `source_id` | `quebec-msss` |
| `status` | `error` |
| `last_run` | `2026-06-04T23:33:38.599Z` |
| `last_success_run` | `2026-06-04T22:38:25.943Z` |
| `last_error_run` | `2026-06-04T23:33:38.599Z` |
| `last_error_category` | `upstream_unavailable` |
| `last_error_stage` | `fetch` |
| `consecutive_failures` | `1` |
| `error_message` | Quebec endpoint returned `403 Forbidden` on the last production scraper run |

## Baseline Scheduler Evidence

| Workflow | Baseline trigger | Latest pre-fix run | Conclusion |
| --- | --- | --- | --- |
| `scraper-cron.yml` | `workflow_dispatch` only; local and remote YAML both say the scheduled trigger is paused to conserve GitHub Actions free-tier minutes | success, created `2026-06-04T23:32:34Z`, updated `2026-06-04T23:39:14Z`, run `26985924241`, <https://github.com/jerdaw/waittimecanada/actions/runs/26985924241> | stale production data is expected unless an operator manually dispatches the workflow |
| `heartbeat-monitor.yml` | `workflow_dispatch` only; local and remote YAML both say the scheduled trigger is paused to conserve GitHub Actions free-tier minutes | failure, created `2026-06-04T23:55:21Z`, updated `2026-06-04T23:55:38Z`, run `26986732670`, <https://github.com/jerdaw/waittimecanada/actions/runs/26986732670> | dead man's switch is also manual-only, so it stopped producing recurring freshness evidence after June 4 |

Preliminary scheduler root cause: scheduled scraper and heartbeat workflows are manual-only, so production freshness decays unless an operator dispatches them.

## Local Dry-Run Evidence

Captured at: 2026-07-08T20:50Z

| Source | Command | Exit | Measurements | Current failure |
| --- | --- | --- | ---: | --- |
| `alberta-ahs` | `.venv/bin/python -m waittime.cli.scraper --source alberta-ahs --dry-run` | 0 | 22 | none |
| `bc-phsa` | `.venv/bin/python -m waittime.cli.scraper --source bc-phsa --dry-run` | 0 | 12 | none |
| `ontario-health` | `.venv/bin/python -m waittime.cli.scraper --source ontario-health --dry-run` | 0 | 166 | none after redirect fix |
| `quebec-msss` | `.venv/bin/python -m waittime.cli.scraper --source quebec-msss --dry-run` | 0 | 205 | none; production `403` is stale June 4 evidence |

## Source-Specific Findings

### Ontario

The old Ontario URL redirects through a multi-hop chain:

1. `https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments`
2. `https://ontariohealth.ca/system-performance/time-spent-in-emergency-departments`
3. `/system/reporting/performance/time-spent-in-emergency-departments.html`
4. `https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments`
5. HTTP 200 with the current page

Root cause: `OntarioScraper._fetch_with_read_timeout()` did not follow redirects, so a manual scraper run from the old remote code would fail on the first `301`.

Fix applied locally:

- `backend/src/waittime/scrapers/ontario.py` now calls `self.client.get(..., follow_redirects=True)`.
- `create_ontario_source()` and `backend/data/sources/ontario-health.json` now use the canonical Ontario Health URL.
- `backend/tests/unit/test_ontario_scraper.py` includes a regression test for the current redirect chain.

### Quebec

Current endpoint probe with the scraper user agent:

| Probe | Result |
| --- | --- |
| URL | Quebec MSSS `type=7382` page 1 endpoint |
| Status | 200 |
| Content type | `text/plain; charset=UTF-8` |
| Bytes | 55,194 |
| `hospital_element` count | 10 |

Conclusion: the production Quebec `403 Forbidden` came from the stale June 4 production run. It did not reproduce from the current local network or scraper dry-run.

## Migration and Source Metadata Findings

`backend/run_migrations.py` maintains a `schema_migrations` checksum ledger. If an already-applied migration file changes, the runner raises `MigrationChecksumMismatchError` with the instruction to create a new migration instead of editing applied history.

Implication: editing `020_sync_active_source_definitions.sql` is not a safe production update path if that migration is already recorded. The old migration has been left with its original HQOntario URL, and a new idempotent migration was added:

- `backend/migrations/022_update_ontario_health_source_url.sql`

That migration updates only `sources.url` for `ontario-health` when the row is not already on the current Ontario Health URL.

Public API source URL exposure check:

| URL | Status | Old URL present | New URL present | Notes |
| --- | --- | --- | --- | --- |
| `https://wait-time.ca/api/sources` | 404 | no | no | no public source endpoint |
| `https://wait-time.ca/api/hospitals` | 200 | no | no | hospital payload does not expose source URL |
| `https://wait-time.ca/api/status` | 200 | no | no | status payload does not expose source URL |
| `https://wait-time.ca/api/health` | 200 | no | no | health payload does not expose source URL |

## Local Verification Before Production Action

Captured after the Ontario redirect fix and migration update:

| Check | Command | Result |
| --- | --- | --- |
| Ruff | `.venv/bin/ruff check src tests/unit/test_ontario_scraper.py tests/unit/test_source_consistency.py` | passed |
| Mypy | `.venv/bin/mypy src` | passed: no issues in 49 source files |
| Focused tests | `.venv/bin/pytest tests/unit/test_ontario_scraper.py tests/unit/test_source_consistency.py -q` | passed: 23 tests |
| Migration sequence | `.venv/bin/python scripts/check_migration_sequence.py` | passed |
| All-source scraper dry-run | `.venv/bin/python -m waittime.cli.scraper --all --dry-run` | passed: 404 measurements from 4 sources (`alberta-ahs=22`, `bc-phsa=12`, `ontario-health=166`, `quebec-msss=204`) |
