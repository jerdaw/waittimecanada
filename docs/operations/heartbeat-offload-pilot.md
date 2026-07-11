# Source Freshness Offload Pilot

This guide is the public, repo-side contract for the ADR-0027 source-freshness
offload pilot. It documents how a trusted non-GitHub runner should invoke the
existing scraper, heartbeat checker, aggregate refresh, and smoke checks without
exposing private infrastructure, credentials, or monitoring configuration.

This is not a private deployment runbook. Runner registration, secret values,
alert routing, private log retention, and service scheduling belong in the
private/shared operations source of truth.

## Command Contract

Use a generic trusted timer service runner for the durable target. The public
wrapper is intentionally repo-safe and prints only environment variable
presence, never values:

```bash
python3 scripts/waittime-freshness-runner.py check
python3 scripts/waittime-freshness-runner.py watchdog --dry-run
python3 scripts/waittime-freshness-runner.py scrape
python3 scripts/waittime-freshness-runner.py aggregate
python3 scripts/waittime-freshness-runner.py smoke
```

The runner uses these public-safe defaults:

- unsafe recovery threshold: 90 minutes
- hard stale threshold: 120 minutes
- freshness scraper timer: hourly at minute 17
- freshness watchdog timer: minutes 07 and 37 every hour
- daily aggregate timer: 06:10 UTC
- lock file: `/tmp/waittime-freshness-runner.lock`

The backend package must be installed in the private runner environment before
operational commands run:

Required environment variable names:

- `DATABASE_URL`

Optional environment variable names:

- `SENTRY_DSN`
- `ALERT_API_URL`
- `ALERT_USER_KEY`
- `ALERT_API_TOKEN`
- `OPERATIONAL_NOTIFICATION_MODE` (`critical_only` for offloaded freshness
  monitoring)

Do not print environment values, connection strings, tokens, webhook URLs, or
private runner details in logs.

## Exit Codes

- `0`: freshness is safe, or an idempotent command completed successfully.
- `1`: health check or command execution failed before a safe/unsafe decision.
- `2`: `/api/health` is unhealthy or source freshness age is at least 90
  minutes.

Treat non-zero as an operational signal for review. It is not a clinical or
triage signal and must not be presented as care guidance.

## Safety Rules

- Run only trusted branch, tag, or manually approved operational jobs on the
  private runner.
- Do not run fork pull-request code or untrusted branch code on the private
  runner.
- Prefer isolated container or disposable execution for jobs that run repository
  code.
- Keep the GitHub `workflow_dispatch` version in
  `.github/workflows/scraper-cron.yml` and `.github/workflows/heartbeat-monitor.yml`
  as fallback entry points until the offloaded job has completed one normal
  operating cycle.
- Keep public summaries concise and free of private paths, private hostnames,
  tokens, database URLs, and alert-route details.

## Runner Isolation

Before a secret-bearing invocation, record the selected runner's controls in
the private/shared operations source of truth. The record must identify a
dedicated least-privilege service identity, protected checkout or immutable
artifact, exact approved revision, writable boundaries, concurrency/locking
control, network dependencies, update owner, and tested isolation mechanism.

The runner must not execute fork pull-request code, arbitrary branches, or a
revision selected by untrusted input. Do not copy sandbox settings blindly:
verify that each control is compatible with the shared lock and the selected
runner before enablement.

## Secret Handling

Record only required environment-variable names and `SET`/`UNSET` presence.
The private record must identify the protected secret source, least-privilege
reader, ownership/access mode, rotation owner, revocation path, and redaction
review without copying any value.

Do not store values in the checkout, unit text, command line, shell history,
logs, failure summaries, screenshots, evidence records, or pull requests.
Disable or avoid shell tracing and environment dumps. If a value is exposed,
stop the pilot, restrict the artifact, notify the owner, and use the separate
credential-rotation procedure; do not repeat the value in an incident record.

## Log Retention

Before enablement, choose a private log sink and record its readers, UTC clock
source, retention duration, rotation/size limits, disk-pressure behavior,
expiry owner, and bounded per-invocation retrieval method. Retain only the
fields needed to diagnose scheduling and freshness behavior.

Logs must exclude environment dumps, command tracing, secret values, database
or alert URLs, unnecessary upstream payloads, and full private response bodies.
A failed log write must be visible as a failure or a separately reviewable
status, not silently reported as a healthy invocation.

## Failure Summaries

Create a bounded, redacted summary for each non-zero invocation instead of
copying raw logs. Minimum fields are **job name, approved revision, exit code**,
start/end time or duration, failure class, public freshness age when available,
fallback decision, follow-up owner/state, redaction reviewer, and a private
evidence reference.

Summaries must not include secret values, private hostnames or paths in public
artifacts, connection strings, tokens, raw environment output, or unreviewed
log dumps. Repeated identical failures should update one active record with
timestamps/counts rather than create duplicate alert noise.

## Rollback Procedure

Rollback is schedule-level, not data repair. Trigger rollback for stale or
missed invocations, unsafe secret/log behavior, lock overlap, failed smoke, or
operator loss of confidence.

1. Record a value-free trigger summary and confirm whether an invocation is
   still active.
2. Stop and disable only the selected offloaded timers; confirm no invocation
   remains active.
3. Preserve bounded logs and configuration for review. Do not delete runner
   state, credentials, or application data during containment.
4. Keep or restore the reviewed GitHub schedule until another accepted soak,
   and keep GitHub `workflow_dispatch` available.
5. If freshness requires recovery, use the existing authorized manual scraper
   workflow and verify the public health timestamp plus production smoke.
6. Keep the standalone safety monitor until a replacement runner completes a
   new 24-hour soak.

Direct database repair, credential rotation, destructive cleanup, and repeated
blind retries require separate cause-specific procedures and authorization.

## Pilot Checklist

1. Complete the private runner isolation, secret handling, log retention,
   failure-summary, and rollback record.
2. Provision the trusted runner outside this public repository.
3. Clone or update the approved revision on the trusted runner.
4. Configure the required `DATABASE_URL` secret and optional secrets in the
   private runner environment file referenced by the local timer units.
5. Install backend dependencies:

   ```bash
   cd backend
   python -m pip install "uv==0.11.23"
   uv sync --locked --no-dev
   ```

6. Run the public-safe checks:

   ```bash
   python3 scripts/waittime-freshness-runner.py check
   python3 scripts/waittime-freshness-runner.py watchdog --dry-run
   ```

7. Confirm dry-run logs contain no secret values, private paths, private
   hostnames, tokens, database URLs, or alert-route details.
8. Run one real private scrape:

   ```bash
   python3 scripts/waittime-freshness-runner.py scrape
   python3 scripts/waittime-freshness-runner.py smoke
   ```

9. Enable the trusted-runner timers only after the manual offloaded run
   behaves as expected.
10. Complete a 24-hour soak with no stale breach and no temporary monitor
   intervention.
11. Exercise or review the rollback path with value-free evidence before
    fallback removal.
12. Remove GitHub scheduled triggers only after the private runner completes
    the 24-hour soak. Keep GitHub `workflow_dispatch` fallback available.

## Copy/Adapt Examples

Generic trusted-timer examples are available under `docs/operations/examples/`:

- `waittime-freshness-scraper.service`
- `waittime-freshness-scraper.timer`
- `waittime-freshness-watchdog.service`
- `waittime-freshness-watchdog.timer`
- `waittime-freshness-aggregate.service`
- `waittime-freshness-aggregate.timer`

They are intentionally stored under `docs/operations/examples/`, so merging this
repository change cannot start a private runner job.

The older copy/adapt Forgejo-style heartbeat example remains at
[examples/forgejo-heartbeat-monitor.yml](examples/forgejo-heartbeat-monitor.yml)
for ADR-0027 historical context only. The durable source-freshness target is the
trusted timer runner described above.

## Related Documents

- [ADR-0027: Hybrid CI Offload Strategy](../adr/0027-hybrid-ci-offload-strategy.md)
- [Scraper Scheduling and Source Freshness](scraper-scheduling.md)
- [Manual Tasks](../planning/manual-tasks.md)
