# WaitTime Health Investigation - 2026-07-08

## Executive Summary

Production health was critical because:

1. The scraper and heartbeat workflows had their scheduled triggers paused and were `workflow_dispatch` only.
2. Production scraper data had not been refreshed since June 4, 2026, leaving all source heartbeat ages far outside the public freshness threshold.
3. A manual scraper run from the old remote code would hit the current Ontario redirect chain unless the Ontario scraper followed redirects.

Current pre-refresh status:

- Scraper scheduler: manual-only by design while GitHub Actions free-tier minutes are conserved.
- Scraper source behavior: all four sources collect current data in local no-DB dry-runs after the Ontario redirect fix.
- Production database freshness: stale until a workflow using the fixed code writes new measurements and heartbeats.
- Remaining recurrence decision: choose manual-only, restored GitHub cron, reduced GitHub cron, or another approved scheduler.

## Root-Cause Table

| Finding | Evidence | Current or stale | Severity | Follow-up |
| --- | --- | --- | --- | --- |
| Scheduled scraper paused | Local and remote workflow YAML show `workflow_dispatch` only; latest scraper run was `2026-06-04T23:32:34Z` | current | high | decide recurrence strategy; dispatch manually for immediate recovery |
| Heartbeat monitor paused | Local and remote workflow YAML show `workflow_dispatch` only; latest heartbeat run was `2026-06-04T23:55:21Z` | current | high | dispatch after scraper refresh or restore cadence |
| Ontario redirect handling | Old source URL redirects through Ontario Health before returning 200; original fetch path did not follow redirects | current until fixed | high | merge/push redirect fix before production scraper dispatch |
| Quebec 403 | Production last error is from `2026-06-04T23:33:38.599Z`; current endpoint probe returns 200 and local dry-run collects data | stale | medium | no scraper fix needed unless production run reproduces |
| DB source URL metadata | Migration runner rejects checksum changes to applied migrations; source URL update requires a new migration | current | medium | apply `022_update_ontario_health_source_url.sql` through normal migration workflow |

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
