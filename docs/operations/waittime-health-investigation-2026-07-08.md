# WaitTime Health Investigation - 2026-07-08

## Executive Summary

Production health was critical because:

1. The scraper and heartbeat workflows had their scheduled triggers paused and were `workflow_dispatch` only.
2. Production scraper data had not been refreshed since June 4, 2026, leaving all source heartbeat ages far outside the public freshness threshold.
3. A manual scraper run from the old remote code would hit the current Ontario redirect chain unless the Ontario scraper followed redirects.

Recovery status after the 2026-07-08 fix:

- Scraper source behavior: all four sources collect current data locally and in the production scraper workflow after the Ontario redirect fix.
- Production database freshness: `/api/health` is healthy with all four source heartbeats refreshed at `2026-07-08T20:58Z`.
- Recurrence: `scraper-cron.yml` is restored to hourly schedule plus manual dispatch; `heartbeat-monitor.yml` is restored to a 30-minute schedule plus manual dispatch.
- Residual public status: `/api/status` and `/api/data-quality` still report `critical` immediately after one successful run because their 24-hour uptime calculation expects 24 hourly windows. They should recover as successful hourly runs accumulate.

## Root-Cause Table

| Finding | Evidence | Current or stale | Severity | Follow-up |
| --- | --- | --- | --- | --- |
| Scheduled scraper paused | Local and remote workflow YAML showed `workflow_dispatch` only; latest scraper run before recovery was `2026-06-04T23:32:34Z` | fixed | high | hourly schedule restored in `6ad2fa2`; manual dispatch remains available |
| Heartbeat monitor paused | Local and remote workflow YAML showed `workflow_dispatch` only; latest heartbeat run before recovery was `2026-06-04T23:55:21Z` | fixed | high | 30-minute schedule restored in `6ad2fa2`; manual dispatch run `28976114340` passed |
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

Invoke-RestMethod -Uri 'https://wait-time.ca/api/health' -TimeoutSec 20
Invoke-RestMethod -Uri 'https://wait-time.ca/api/status' -TimeoutSec 20
```

## Recovery Evidence

Captured at: 2026-07-08T21:13Z

| Item | Evidence | Result |
| --- | --- | --- |
| Redirect/source fix | Commit `3a3f63b` | Ontario scraper follows redirects and source metadata points to the current Ontario Health URL |
| Investigation record | Commit `c0e229d` | Baseline, dry-run, migration, and production action evidence recorded |
| Recurrence fix | Commit `6ad2fa2` | Scraper schedule restored to hourly; heartbeat schedule restored to every 30 minutes |
| Migration workflow | Run `28975179871`, <https://github.com/jerdaw/waittimecanada/actions/runs/28975179871> | success |
| Production scraper workflow | Run `28975214976`, <https://github.com/jerdaw/waittimecanada/actions/runs/28975214976> | success; 403 did not recur; all four source heartbeats refreshed |
| Heartbeat workflow | Run `28976114340`, <https://github.com/jerdaw/waittimecanada/actions/runs/28976114340> | success on restored workflow definition |
| Production smoke workflow | Run `28976114348`, <https://github.com/jerdaw/waittimecanada/actions/runs/28976114348> | success against `https://wait-time.ca` |
| Docs CI | Run `28976106659`, <https://github.com/jerdaw/waittimecanada/actions/runs/28976106659> | success after recurrence docs update |

Post-refresh API state:

| Endpoint | Observed status | Key evidence | Interpretation |
| --- | --- | --- | --- |
| `/api/health` | 200, healthy | `last_update=2026-07-08T20:58:43.455Z`; source ages about 14-15 minutes at the 21:13Z check; source counts: AB 22, BC 11, ON 166, QC 204 | current scraper freshness recovered |
| `/api/status` | 200, critical | `system_uptime_24h=0.042`; `scheduler_cadence=hourly`; `expected_runs_24h=24`; all source heartbeats healthy | current freshness is healthy, but the 24-hour success-rate window contains only one successful hourly run after a month-long gap |
| `/api/data-quality` | 200, critical | `system_uptime_24h=0.042`; `total_measurements_24h=403`; all source heartbeats healthy | measurements are flowing again, but the 24-hour data-quality success-rate window needs recurring hourly runs to recover |

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

## Scheduler Evidence

| Workflow | Current trigger | Latest run | Conclusion |
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
