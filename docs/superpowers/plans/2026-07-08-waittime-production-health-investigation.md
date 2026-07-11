# WaitTime Production Health Investigation Implementation Plan

**Status:** Historical execution plan; closed on 2026-07-10

This checklist is retained as incident history. Do not execute the unchecked
steps as an active plan. Recovery evidence and the resulting conclusions are
recorded in
`docs/operations/waittime-health-investigation-2026-07-08.md`. Remaining
trusted-runner, observation, and operator-dependent work is tracked only in
`docs/planning/roadmap.md` and `docs/planning/manual-tasks.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine why Wait Time Canada production health is critical, prove which failures are current versus stale, identify the exact recovery path, and leave durable evidence for scheduler/source/metadata follow-up.

**Architecture:** Treat this as a multi-layer incident investigation: public API symptoms, GitHub Actions scheduler state, scraper source behavior, database/source metadata, and post-refresh production verification. Do not inspect secret files; use GitHub workflow secrets only through existing workflows, and use dry-runs for local scraper validation.

**Tech Stack:** Python 3.12, pytest, ruff, mypy, httpx, GitHub Actions, GitHub CLI, Next.js API routes, PostgreSQL-backed production data exposed through `/api/health`, `/api/status`, and `/api/data-quality`.

## Global Constraints

- Never read `.env`, `.env.local`, key, certificate, or private credential files.
- Local framework/tooling may auto-load trusted env during normal commands, but do not print, inspect, summarize, copy, or persist secret values.
- Production deploys and database writes must be explicit operator actions.
- Keep scraper runtime changes covered by failing tests first.
- Scheduled operational workflows are intentionally paused until quota/cadence is decided.
- Public docs and private operations notes have different boundaries; do not move private deployment details into public docs.
- Do not claim recovery until public endpoints and workflow logs show current successful evidence.

---

### Task 1: Capture Current Production Symptom Baseline

**Files:**
- Create or append: `docs/operations/waittime-health-investigation-2026-07-08.md`
- Read only: public production endpoints

**Interfaces:**
- Consumes: public HTTP responses from `https://wait-time.ca/api/health`, `https://wait-time.ca/api/status`, and `https://wait-time.ca/api/data-quality`
- Produces: an evidence note with exact timestamps, status codes, source ages, and response classifications

- [ ] **Step 1: Create the evidence note header**

```markdown
# WaitTime Health Investigation - 2026-07-08

## Baseline

- Captured at:
- Operator:
- Public base URL: https://wait-time.ca

## Public API Evidence
```

- [ ] **Step 2: Capture `/api/health` without secrets**

Run:

```powershell
$health = Invoke-RestMethod -Uri 'https://wait-time.ca/api/health' -TimeoutSec 20
[pscustomobject]@{
  healthy = $health.healthy
  last_update = $health.last_update
  source_count = $health.sources.Count
  statuses = ($health.sources | ForEach-Object {
    "$($_.source_id):$($_.status):$($_.age_minutes)m:last_run=$($_.last_run)"
  }) -join ', '
} | Format-List
```

Expected investigation result:

```text
healthy: False
sources include alberta-ahs, bc-phsa, ontario-health, quebec-msss
all age_minutes values are much larger than the configured freshness threshold
```

- [ ] **Step 3: Capture `/api/status`**

Run:

```powershell
$status = Invoke-RestMethod -Uri 'https://wait-time.ca/api/status' -TimeoutSec 20
[pscustomobject]@{
  overall_status = $status.overall_status
  generated_at = $status.generated_at
  source_ages = ($status.sources | ForEach-Object {
    "$($_.source_id):$($_.last_heartbeat_age_minutes)m:status=$($_.scraper_status)"
  }) -join ', '
} | Format-List
```

Expected investigation result:

```text
overall_status: critical
all source heartbeat ages are stale
```

- [ ] **Step 4: Capture `/api/data-quality`**

Run:

```powershell
$dq = Invoke-RestMethod -Uri 'https://wait-time.ca/api/data-quality' -TimeoutSec 20
$dq | ConvertTo-Json -Depth 5
```

Expected investigation result:

```text
The response is captured exactly enough to determine whether the critical state is only heartbeat freshness or also aggregate/data-quality drift.
```

- [ ] **Step 5: Append baseline findings to the evidence note**

Append a concise table:

```markdown
| Endpoint | Observed status | Key evidence | Interpretation |
| --- | --- | --- | --- |
| `/api/health` | 200, unhealthy | source ages copied from Step 2 output | scraper freshness failure |
| `/api/status` | 200, critical | heartbeat ages copied from Step 3 output | production status reflects stale heartbeat |
| `/api/data-quality` | status code and body classification copied from Step 4 output | aggregate/data-quality evidence copied from Step 4 output | classify as recovered, degraded, or unrelated |
```

- [ ] **Step 6: Commit only if an evidence note was created**

Run:

```bash
git add docs/operations/waittime-health-investigation-2026-07-08.md
git commit -m "docs: capture waittime production health baseline"
```

Expected:

```text
Commit succeeds, or this step is skipped if investigation notes remain local only.
```

### Task 2: Confirm GitHub Actions Scheduler State

**Files:**
- Read only: `.github/workflows/scraper-cron.yml`
- Read only: `.github/workflows/heartbeat-monitor.yml`
- Read only: `.github/workflows/README.md`
- Append evidence: `docs/operations/waittime-health-investigation-2026-07-08.md`

**Interfaces:**
- Consumes: workflow YAML, GitHub Actions run history
- Produces: a determination of whether stale production data is caused by an intentionally paused schedule, workflow failure, disabled workflow, or missing manual dispatch

- [ ] **Step 1: Confirm workflow triggers in local YAML**

Run:

```powershell
Get-Content -Raw .github\workflows\scraper-cron.yml
Get-Content -Raw .github\workflows\heartbeat-monitor.yml
Get-Content -Raw .github\workflows\README.md
```

Expected:

```text
scraper-cron.yml and heartbeat-monitor.yml use workflow_dispatch only.
README states scheduled triggers are paused to conserve GitHub Actions free-tier minutes.
```

- [ ] **Step 2: Confirm workflow trigger state from GitHub**

Run:

```powershell
gh workflow view scraper-cron.yml --repo jerdaw/waittimecanada --yaml |
  Select-String -Pattern 'schedule|workflow_dispatch|paused|cron|Run scrapers' -Context 2,2
gh workflow view heartbeat-monitor.yml --repo jerdaw/waittimecanada --yaml |
  Select-String -Pattern 'schedule|workflow_dispatch|paused|heartbeat|cron' -Context 2,2
```

Expected:

```text
Remote workflow YAML matches local workflow_dispatch-only state.
```

- [ ] **Step 3: Inspect scraper run history**

Run:

```powershell
gh run list --repo jerdaw/waittimecanada --workflow scraper-cron.yml --limit 20 `
  --json databaseId,status,conclusion,createdAt,updatedAt,event,displayTitle,headBranch,url
```

Expected:

```text
Most recent scraper run timestamp lines up with the production last_update timestamp.
No newer manual dispatch appears after the schedule pause.
```

- [ ] **Step 4: Inspect heartbeat run history**

Run:

```powershell
gh run list --repo jerdaw/waittimecanada --workflow heartbeat-monitor.yml --limit 20 `
  --json databaseId,status,conclusion,createdAt,updatedAt,event,displayTitle,headBranch,url
```

Expected:

```text
Heartbeat runs stop near the same time as scraper runs, or any newer heartbeat run confirms stale production data.
```

- [ ] **Step 5: Record root-cause classification**

Append:

```markdown
## Scheduler Evidence

| Workflow | Current trigger | Latest run | Conclusion |
| --- | --- | --- | --- |
| scraper-cron.yml | workflow_dispatch only | latest run timestamp and URL copied from `gh run list` | stale data expected unless manually dispatched |
| heartbeat-monitor.yml | workflow_dispatch only | latest run timestamp and URL copied from `gh run list` | dead man's switch is also manual-only |

Preliminary scheduler root cause: scheduled scraper and heartbeat workflows are manual-only, so production freshness decays unless an operator dispatches them.
```

### Task 3: Reproduce Scraper Behavior Locally Without Database Writes

**Files:**
- Read only: `backend/src/waittime/cli/scraper.py`
- Read only: `backend/src/waittime/scrapers/`
- Append evidence: `docs/operations/waittime-health-investigation-2026-07-08.md`

**Interfaces:**
- Consumes: local virtualenv, public upstream data sources
- Produces: per-source dry-run evidence showing which scrapers currently collect data without touching production DB

- [ ] **Step 1: Confirm local environment without reading secrets**

Run:

```powershell
Get-ChildItem -Force backend
Get-ChildItem -Force backend\.venv
```

Expected:

```text
backend/.venv exists.
Do not open backend/.env or any .env file.
```

- [ ] **Step 2: Run Quebec dry-run**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python -m waittime.cli.scraper --source quebec-msss --dry-run
```

Expected:

```text
Exit code 0.
Collected a nonzero number of Quebec measurements.
If it fails with 403, capture full exception category and current endpoint headers.
```

- [ ] **Step 3: Run Ontario dry-run**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python -m waittime.cli.scraper --source ontario-health --dry-run
```

Expected:

```text
Exit code 0.
Collected a nonzero number of Ontario measurements.
If it fails with a 301/302 redirect, proceed to Task 4.
```

- [ ] **Step 4: Run all-source dry-run**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python -m waittime.cli.scraper --all --dry-run
```

Expected:

```text
Exit code 0.
All four sources collect data.
Any warnings about generated hospital IDs are recorded separately from scraper failure.
```

- [ ] **Step 5: Append dry-run matrix**

Append:

```markdown
## Local Dry-Run Evidence

| Source | Command | Exit | Measurements | Current failure |
| --- | --- | --- | ---: | --- |
| alberta-ahs | `--source alberta-ahs --dry-run` | record exit code | record collected measurement count | record exception text or `none` |
| bc-phsa | `--source bc-phsa --dry-run` | record exit code | record collected measurement count | record exception text or `none` |
| ontario-health | `--source ontario-health --dry-run` | record exit code | record collected measurement count | record exception text or `none` |
| quebec-msss | `--source quebec-msss --dry-run` | record exit code | record collected measurement count | record exception text or `none` |
```

### Task 4: Investigate Ontario Redirect and Runtime Source Metadata

**Files:**
- Read: `backend/src/waittime/scrapers/ontario.py`
- Read: `backend/tests/unit/test_ontario_scraper.py`
- Read: `backend/data/sources/ontario-health.json`
- Read: `backend/migrations/020_sync_active_source_definitions.sql`
- Modify only if the bug is present: the same four files

**Interfaces:**
- Consumes: public Ontario Health URL chain and local `OntarioScraper.fetch()`
- Produces: a tested conclusion on whether Ontario failures are due to redirect handling, stale source URL metadata, parser breakage, or upstream content changes

- [ ] **Step 1: Probe old and current Ontario URL chain**

Run:

```bash
curl -sS -I -L --max-redirs 10 --max-time 20 \
  'https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments'

curl -sS -I -L --max-redirs 10 --max-time 20 \
  'https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments'
```

Expected:

```text
The old URL redirects through ontariohealth.ca.
The canonical URL eventually returns HTTP 200.
```

- [ ] **Step 2: Write or confirm failing redirect regression test**

Expected test shape in `backend/tests/unit/test_ontario_scraper.py`:

```python
def test_fetch_follows_current_ontario_redirect_chain(self, scraper):
    final_html = "<html><table><tr><td>CHEO</td><td>0.5</td></tr></table></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        request_url = str(request.url)
        if request_url == "https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments":
            return httpx.Response(
                301,
                headers={
                    "Location": (
                        "https://ontariohealth.ca/system-performance/"
                        "time-spent-in-emergency-departments"
                    )
                },
                request=request,
            )
        if request_url == "https://ontariohealth.ca/system-performance/time-spent-in-emergency-departments":
            return httpx.Response(
                301,
                headers={
                    "Location": (
                        "/system/reporting/performance/"
                        "time-spent-in-emergency-departments.html"
                    )
                },
                request=request,
            )
        if (
            request_url
            == "https://ontariohealth.ca/system/reporting/performance/"
            "time-spent-in-emergency-departments.html"
        ):
            return httpx.Response(
                301,
                headers={
                    "Location": (
                        "https://ontariohealth.ca/system/reporting/performance/"
                        "time-spent-in-emergency-departments"
                    )
                },
                request=request,
            )
        if (
            request_url
            == "https://ontariohealth.ca/system/reporting/performance/"
            "time-spent-in-emergency-departments"
        ):
            return httpx.Response(200, text=final_html, request=request)
        return httpx.Response(404, request=request)

    scraper.client.close()
    scraper.client = httpx.Client(transport=httpx.MockTransport(handler))

    assert scraper.fetch() == final_html
```

- [ ] **Step 3: Run the redirect test before any fix**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/pytest tests/unit/test_ontario_scraper.py::TestOntarioScraper::test_fetch_follows_current_ontario_redirect_chain -q
```

Expected if bug is present:

```text
FAIL with httpx.HTTPStatusError or tenacity.RetryError caused by HTTP 301.
```

- [ ] **Step 4: Fix redirect handling only if the test fails for the expected reason**

Expected minimal implementation in `backend/src/waittime/scrapers/ontario.py`:

```python
response = self.client.get(
    target_url,
    timeout=httpx.Timeout(
        connect=DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS,
        read=read_timeout_seconds,
        write=DEFAULT_HTTP_WRITE_TIMEOUT_SECONDS,
        pool=DEFAULT_HTTP_POOL_TIMEOUT_SECONDS,
    ),
    follow_redirects=True,
)
```

- [ ] **Step 5: Update canonical runtime URL if old metadata is still active**

Expected value in `create_ontario_source()`, `backend/data/sources/ontario-health.json`, and any active source-sync migration used by fresh DB bootstrap:

```text
https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/pytest tests/unit/test_ontario_scraper.py tests/unit/test_source_consistency.py -q
```

Expected:

```text
All tests pass.
```

- [ ] **Step 7: Run live Ontario dry-run**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python -m waittime.cli.scraper --source ontario-health --dry-run
```

Expected:

```text
Exit code 0 and nonzero Ontario measurement count.
```

### Task 5: Investigate Quebec 403 as Current Failure or Stale Evidence

**Files:**
- Read: `backend/src/waittime/scrapers/quebec.py`
- Read: `backend/tests/unit` tests involving Quebec scraper if present
- Append evidence: `docs/operations/waittime-health-investigation-2026-07-08.md`

**Interfaces:**
- Consumes: production health `last_error_*` fields, public Quebec endpoint response, local Quebec dry-run
- Produces: a determination of whether Quebec currently fails, or whether production only reports stale June 4 error state

- [ ] **Step 1: Capture production Quebec error fields**

Run:

```powershell
$health = Invoke-RestMethod -Uri 'https://wait-time.ca/api/health' -TimeoutSec 20
$health.sources | Where-Object source_id -eq 'quebec-msss' | ConvertTo-Json -Depth 5
```

Expected:

```text
Fields include last_error_run, last_error_category, last_error_stage, consecutive_failures, and last_success_run.
```

- [ ] **Step 2: Probe Quebec endpoint with scraper-like user agent**

Run:

```powershell
$url = 'https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec?id=24981&tx_solr%5Blocation%5D=&tx_solr%5Bpt%5D=&tx_solr%5Bsfield%5D=geolocation_location&tx_solr%5Bpage%5D=1&type=7382'
$headers = @{ 'User-Agent' = 'WaitTimeCanada/1.0 (Health Systems Observatory; +https://wait-time.ca)' }
$r = Invoke-WebRequest -Uri $url -Headers $headers -TimeoutSec 20 -SkipHttpErrorCheck
[pscustomobject]@{
  StatusCode = $r.StatusCode
  ContentType = $r.Headers['Content-Type']
  Bytes = $r.Content.Length
  HospitalElements = ([regex]::Matches($r.Content, 'hospital_element').Count)
} | Format-List
```

Expected if the production error is stale:

```text
StatusCode: 200
HospitalElements: greater than 0
```

- [ ] **Step 3: Run local Quebec dry-run**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python -m waittime.cli.scraper --source quebec-msss --dry-run
```

Expected:

```text
Exit code 0 and nonzero Quebec measurement count.
```

- [ ] **Step 4: If Quebec still fails, trace failure stage**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python - <<'PY'
from waittime.scrapers.quebec import QuebecScraper, create_quebec_source

with QuebecScraper(create_quebec_source()) as scraper:
    html = scraper._fetch_page(1)
    print(len(html))
    print(html.count("hospital_element"))
    print(scraper.parse(html)[:3])
PY
```

Expected:

```text
If fetch fails, root cause is upstream access.
If fetch succeeds but parse count is zero, root cause is parser structure drift.
```

### Task 6: Investigate Production DB Source Metadata and Migration State

**Files:**
- Read: `backend/data/sources/ontario-health.json`
- Read: `backend/migrations/020_sync_active_source_definitions.sql`
- Potentially create: `backend/migrations/0NN_update_ontario_health_source_url.sql`
- Potentially test: migration sequence guard

**Interfaces:**
- Consumes: current production source metadata exposed by public APIs or DB-backed workflow checks
- Produces: a decision on whether a new migration is needed because editing an already-applied historical migration will not update production

- [ ] **Step 1: Determine whether production exposes source URL publicly**

Run:

```powershell
$candidateUrls = @(
  'https://wait-time.ca/api/sources',
  'https://wait-time.ca/api/hospitals',
  'https://wait-time.ca/api/status',
  'https://wait-time.ca/api/health'
)
foreach ($url in $candidateUrls) {
  try {
    $r = Invoke-WebRequest -Uri $url -TimeoutSec 20 -SkipHttpErrorCheck
    [pscustomobject]@{ Url = $url; Status = $r.StatusCode; HasOldUrl = $r.Content.Contains('hqontario.ca/system-performance/time-spent-in-emergency-departments'); HasNewUrl = $r.Content.Contains('ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments') }
  } catch {
    [pscustomobject]@{ Url = $url; Status = 'error'; HasOldUrl = $false; HasNewUrl = $false }
  }
}
```

Expected:

```text
Either no public source URL is exposed, or the old/new URL state is known.
```

- [ ] **Step 2: Check migration tracking behavior before editing old migration further**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
rg -n "schema_migrations|applied_migrations|migration" run_migrations.py migrations src -S
```

Expected:

```text
The migration runner's applied-migration tracking model is understood.
```

- [ ] **Step 3: If production will not rerun migration 020, write a new idempotent migration**

Expected file name pattern:

```text
backend/migrations/0NN_update_ontario_health_source_url.sql
```

Expected SQL:

```sql
-- 0NN_update_ontario_health_source_url.sql
-- Align Ontario active source URL with current Ontario Health reporting path.

UPDATE sources
SET
    url = 'https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments',
    updated_at = NOW()
WHERE
    id = 'ontario-health'
    AND url <> 'https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments';

-- Rollback:
-- UPDATE sources
-- SET url = 'https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments',
--     updated_at = NOW()
-- WHERE id = 'ontario-health';
```

- [ ] **Step 4: Verify migration sequence**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python scripts/check_migration_sequence.py
```

Expected:

```text
Migration sequence check passed.
```

- [ ] **Step 5: Decide whether to run `database-migrate.yml`**

Run only after the migration is committed and pushed:

```powershell
gh workflow run database-migrate.yml --repo jerdaw/waittimecanada --ref main
gh run list --repo jerdaw/waittimecanada --workflow database-migrate.yml --limit 1
```

Expected:

```text
Migration workflow is not run from uncommitted local changes.
If run, the workflow succeeds before scraper refresh.
```

### Task 7: Verify Local Code Quality Before Production Action

**Files:**
- Read/verify: backend source and tests touched by investigation

**Interfaces:**
- Consumes: local code state
- Produces: evidence that the branch is safe to push or hand off

- [ ] **Step 1: Run ruff**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/ruff check src tests/unit/test_ontario_scraper.py tests/unit/test_source_consistency.py
```

Expected:

```text
All checks passed!
```

- [ ] **Step 2: Run mypy**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/mypy src
```

Expected:

```text
Success: no issues found in source files.
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/pytest tests/unit/test_ontario_scraper.py tests/unit/test_source_consistency.py -q
```

Expected:

```text
All tests pass.
```

- [ ] **Step 4: Run full dry-run**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/python -m waittime.cli.scraper --all --dry-run
```

Expected:

```text
Exit code 0.
All four source scrapers collect nonzero measurements.
```

### Task 8: Determine Safe Production Refresh Path

**Files:**
- Read: `.github/workflows/scraper-cron.yml`
- Read: `.github/workflows/production-smoke.yml`
- Read: `.github/workflows/database-migrate.yml`
- Append evidence: `docs/operations/waittime-health-investigation-2026-07-08.md`

**Interfaces:**
- Consumes: committed code state, GitHub Actions workflow definitions, run history
- Produces: a go/no-go checklist for production refresh

- [ ] **Step 1: Confirm local changes are committed and pushed before dispatch**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada
git status --short
git log --oneline -3
git rev-parse HEAD
gh run list --repo jerdaw/waittimecanada --branch main --limit 3
```

Expected:

```text
No required fix exists only in the local working tree.
The workflow ref to be dispatched contains the Ontario redirect fix.
```

- [ ] **Step 2: Confirm workflow can access required secrets without printing values**

Run:

```powershell
gh secret list --repo jerdaw/waittimecanada
```

Expected:

```text
DATABASE_URL is present.
Do not print or inspect secret values.
```

- [ ] **Step 3: Run database migration first only if Task 6 required a new migration**

Run:

```powershell
gh workflow run database-migrate.yml --repo jerdaw/waittimecanada --ref main
$run = gh run list --repo jerdaw/waittimecanada --workflow database-migrate.yml --limit 1 --json databaseId -q '.[0].databaseId'
gh run watch $run --repo jerdaw/waittimecanada --exit-status
```

Expected:

```text
Migration workflow exits 0, or this step is skipped because no production DB metadata migration is needed.
```

- [ ] **Step 4: Dispatch scraper workflow**

Run:

```powershell
gh workflow run scraper-cron.yml --repo jerdaw/waittimecanada --ref main
$run = gh run list --repo jerdaw/waittimecanada --workflow scraper-cron.yml --limit 1 --json databaseId -q '.[0].databaseId'
gh run watch $run --repo jerdaw/waittimecanada --exit-status
```

Expected:

```text
Workflow exits 0.
Run logs show nonzero measurements for all four source scrapers.
Aggregate refresh step succeeds.
Heartbeat summary step does not report unresolved critical scraper failure.
```

- [ ] **Step 5: Capture workflow logs if scraper workflow fails**

Run:

```powershell
gh run view $run --repo jerdaw/waittimecanada --log > scraper-cron-$run.log
Select-String -Path scraper-cron-$run.log -Pattern 'error|failed|RetryError|HTTPStatusError|Traceback|Collected|measurements' -CaseSensitive:$false
```

Expected:

```text
Failure is classified by source and stage before another fix attempt.
```

### Task 9: Verify Production Recovery After Refresh

**Files:**
- Append evidence: `docs/operations/waittime-health-investigation-2026-07-08.md`

**Interfaces:**
- Consumes: public API state after workflow dispatch
- Produces: proof of recovery or a precise remaining failure classification

- [ ] **Step 1: Poll `/api/health` after scraper workflow completes**

Run:

```powershell
for ($i = 1; $i -le 10; $i++) {
  $health = Invoke-RestMethod -Uri 'https://wait-time.ca/api/health' -TimeoutSec 20
  [pscustomobject]@{
    attempt = $i
    healthy = $health.healthy
    last_update = $health.last_update
    statuses = ($health.sources | ForEach-Object { "$($_.source_id):$($_.status):$($_.age_minutes)m" }) -join ', '
  } | Format-List
  Start-Sleep -Seconds 30
}
```

Expected:

```text
Source ages drop to current freshness range.
If healthy remains false, the remaining source/status is identified.
```

- [ ] **Step 2: Poll `/api/status`**

Run:

```powershell
$status = Invoke-RestMethod -Uri 'https://wait-time.ca/api/status' -TimeoutSec 20
[pscustomobject]@{
  overall_status = $status.overall_status
  generated_at = $status.generated_at
  source_ages = ($status.sources | ForEach-Object { "$($_.source_id):$($_.last_heartbeat_age_minutes)m:status=$($_.scraper_status)" }) -join ', '
} | Format-List
```

Expected:

```text
overall_status no longer critical if all source heartbeats recovered.
```

- [ ] **Step 3: Run production smoke workflow**

Run:

```powershell
gh workflow run production-smoke.yml --repo jerdaw/waittimecanada --ref main -f base_url=https://wait-time.ca
$run = gh run list --repo jerdaw/waittimecanada --workflow production-smoke.yml --limit 1 --json databaseId -q '.[0].databaseId'
gh run watch $run --repo jerdaw/waittimecanada --exit-status
```

Expected:

```text
Production smoke exits 0.
```

- [ ] **Step 4: Append recovery evidence**

Append:

```markdown
## Recovery Evidence

| Check | Result | Evidence |
| --- | --- | --- |
| scraper workflow | success or failure conclusion copied from `gh run watch` | run URL |
| `/api/health` | healthy value and source statuses copied from polling output | source ages |
| `/api/status` | overall status copied from polling output | overall status and generated_at |
| production smoke | success or failure conclusion copied from `gh run watch` | run URL |
```

### Task 10: Investigate Recurrence Strategy for Scheduler Cadence

**Files:**
- Read: `.github/workflows/README.md`
- Read: `.github/workflows/scraper-cron.yml`
- Read: `.github/workflows/heartbeat-monitor.yml`
- Potentially modify after decision: workflow cron blocks or operations docs
- Append evidence: `docs/operations/waittime-health-investigation-2026-07-08.md`

**Interfaces:**
- Consumes: GitHub Actions usage constraints, desired freshness threshold, production source-health requirements
- Produces: a decision record for manual dispatch, restored schedule, reduced schedule, or external scheduler

- [ ] **Step 1: Determine current intended freshness threshold**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada
rg -n "stale_threshold|max-age|scheduler_cadence|expected_runs_24h|120|720" backend frontend docs .github -S
```

Expected:

```text
The threshold used by API status and heartbeat workflows is identified.
```

- [ ] **Step 2: Estimate action minutes for current scraper workflow**

Run:

```powershell
gh run list --repo jerdaw/waittimecanada --workflow scraper-cron.yml --limit 20 `
  --json databaseId,createdAt,updatedAt,conclusion,event |
  ConvertFrom-Json |
  ForEach-Object {
    [pscustomobject]@{
      run = $_.databaseId
      event = $_.event
      conclusion = $_.conclusion
      minutes = ([datetime]$_.updatedAt - [datetime]$_.createdAt).TotalMinutes
    }
  } | Format-Table
```

Expected:

```text
Approximate minutes per scraper run are known.
```

- [ ] **Step 3: Compare cadence options**

Use this decision matrix:

```markdown
| Option | Freshness | Cost/risk | Operational burden | Recommendation |
| --- | --- | --- | --- | --- |
| Manual only | stale unless operator runs | lowest minutes | high | short-term emergency-only option |
| Hourly GitHub cron | best app freshness | high minutes | low | use only if quota budget supports it |
| 4x/day GitHub cron | acceptable if threshold changed | medium | low | likely compromise if freshness copy and thresholds are updated |
| Daily GitHub cron | poor for wait-time app | low | low | not recommended for public wait-time freshness |
| VPS/systemd scraper | good if runtime and secrets are managed | outside GitHub quota | medium | investigate if GitHub quota remains the blocker |
```

- [ ] **Step 4: If restoring GitHub schedule, propose exact YAML**

For hourly:

```yaml
on:
  schedule:
    - cron: "17 * * * *"
  workflow_dispatch:
```

For 4x/day:

```yaml
on:
  schedule:
    - cron: "17 5,11,17,23 * * *"
  workflow_dispatch:
```

Expected:

```text
Any schedule restoration is explicit and paired with an updated threshold/cadence statement if needed.
```

- [ ] **Step 5: Record recurrence recommendation**

Append:

```markdown
## Recurrence Recommendation

Chosen option:
Rationale:
Follow-up change required:
Owner:
```

### Task 11: Investigate Documentation and Public Naming Drift

**Files:**
- Read: `docs/ontario-methodology.md`
- Read: `docs/ontario-research-findings.md`
- Read: `backend/docs/methodologies/ontario-methodology.md`
- Read: `backend/docs/methodologies/ontario-reference.json`
- Read: `frontend/messages/en.json`
- Read: `frontend/messages/fr.json`
- Potentially create a separate docs update plan if the drift is broad

**Interfaces:**
- Consumes: source naming and URL references in public docs/frontend copy
- Produces: a scoped recommendation on whether to update public copy now or split into a documentation pass

- [ ] **Step 1: Search active references**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada
rg -n "HQOntario|Health Quality Ontario|hqontario\\.ca|ontariohealth\\.ca" backend docs frontend .github scripts -S --glob "!.venv/**" --glob "!node_modules/**"
```

Expected:

```text
All active references are listed.
Historical references are separated from runtime metadata and user-facing current copy.
```

- [ ] **Step 2: Classify references**

Use:

```markdown
| Path | Reference | Category | Action |
| --- | --- | --- | --- |
| `backend/src/waittime/scrapers/ontario.py` | runtime metadata | runtime | update with code fix |
| `backend/data/sources/ontario-health.json` | seed metadata | runtime/bootstrap | update with code fix |
| `backend/migrations/020_sync_active_source_definitions.sql` or a new migration | DB metadata | migration | new migration if production already applied old migration |
| `docs/ontario-methodology.md` and `docs/ontario-research-findings.md` | public methodology docs | docs | update in docs pass |
| `frontend/messages/en.json` and `frontend/messages/fr.json` | user-facing copy | frontend copy | decide if name remains acceptable |
```

- [ ] **Step 3: Decide whether public source name should remain `Health Quality Ontario`**

Check:

```text
If Ontario Health has replaced HQO but public methodology still cites HQO historical reporting, keep display name only if it is intentionally historical.
If current source branding is Ontario Health, propose a copy/docs update separately.
```

- [ ] **Step 4: Run docs checks if docs are changed**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada
bash scripts/check-docs.sh
```

Expected:

```text
Docs checks pass, or docs changes are deferred into a separate plan.
```

### Task 12: Final Root-Cause Report and Handoff

**Files:**
- Finalize: `docs/operations/waittime-health-investigation-2026-07-08.md`
- Optionally update: `docs/planning/roadmap.md` only if public project status changes

**Interfaces:**
- Consumes: all prior task evidence
- Produces: a concise root-cause report with current status, completed recovery steps, and remaining owner decisions

- [ ] **Step 1: Write executive summary**

Use:

```markdown
## Executive Summary

Production health was critical because:
1. Scheduled scraper and heartbeat workflows were not running automatically.
2. At least one source-specific scraper failure or stale error needed current dry-run validation before production dispatch.
3. Production freshness could not recover until the workflow ref contained any required scraper/source metadata fixes and the scraper workflow was dispatched.

Current status:
- Scraper scheduler:
- Scraper source behavior:
- Production database freshness:
- Remaining recurrence decision:
```

- [ ] **Step 2: Write root-cause table**

Use:

```markdown
| Finding | Evidence | Current/ stale | Severity | Follow-up |
| --- | --- | --- | --- | --- |
| Scheduled scraper paused | workflow YAML + run history | current | high | choose cadence |
| Ontario redirect handling | dry-run/test evidence | current until patched | high | merge fix |
| Quebec 403 | production last_error from 2026-06-04 plus current dry-run | classify as stale if current dry-run succeeds, current if it fails | medium/high | update scraper only if current repro fails |
| DB source URL metadata | migration/API evidence | classify as current if production still exposes old URL or migration tracking prevents update | medium | new migration if needed |
```

- [ ] **Step 3: Write exact recovery commands used or recommended**

Use:

````markdown
## Operator Commands

```powershell
gh workflow run scraper-cron.yml --repo jerdaw/waittimecanada --ref main
gh run watch <run-id> --repo jerdaw/waittimecanada --exit-status
Invoke-RestMethod -Uri 'https://wait-time.ca/api/health' -TimeoutSec 20
```
````

- [ ] **Step 4: Run final verification commands**

Run:

```bash
cd /home/jer/repos/vps/waittimecanada/backend
.venv/bin/ruff check src tests/unit/test_ontario_scraper.py tests/unit/test_source_consistency.py
.venv/bin/mypy src
.venv/bin/pytest tests/unit/test_ontario_scraper.py tests/unit/test_source_consistency.py -q
.venv/bin/python scripts/check_migration_sequence.py
.venv/bin/python -m waittime.cli.scraper --all --dry-run
```

Expected:

```text
All commands exit 0.
```

- [ ] **Step 5: Commit investigation artifacts and fixes separately**

Recommended commits:

```bash
git add backend/src/waittime/scrapers/ontario.py backend/tests/unit/test_ontario_scraper.py backend/data/sources/ontario-health.json backend/migrations
git commit -m "fix: follow Ontario Health source redirects"

git add docs/operations/waittime-health-investigation-2026-07-08.md
git commit -m "docs: record waittime health investigation"
```

Expected:

```text
Runtime fix and investigation record are reviewable independently.
```

## Self-Review

- Spec coverage: The plan covers current production symptoms, scheduled workflow state, local scraper reproduction, Ontario redirect behavior, Quebec 403 freshness, DB metadata/migration state, production dispatch, post-refresh verification, recurrence strategy, docs drift, and final handoff.
- Placeholder scan: No task contains unresolved placeholder markers. Commands and expected outcomes are explicit.
- Type consistency: Referenced source IDs, file paths, workflow names, and command names are consistent across tasks.
