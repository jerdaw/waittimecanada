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

## Pilot Checklist

1. Provision the trusted runner outside this public repository.
2. Clone or update this repository on the trusted runner.
3. Configure the required `DATABASE_URL` secret and optional secrets in the
   private runner environment file referenced by the local timer units.
4. Install backend dependencies:

   ```bash
   cd backend
   python -m pip install "uv==0.11.23"
   uv sync --locked --no-dev
   ```

5. Run the public-safe checks:

   ```bash
   python3 scripts/waittime-freshness-runner.py check
   python3 scripts/waittime-freshness-runner.py watchdog --dry-run
   ```

6. Confirm dry-run logs contain no secret values, private paths, private
   hostnames, tokens, database URLs, or alert-route details.
7. Run one real private scrape:

   ```bash
   python3 scripts/waittime-freshness-runner.py scrape
   python3 scripts/waittime-freshness-runner.py smoke
   ```

8. Enable the trusted-runner timers only after the manual offloaded run
   behaves as expected.
9. Complete a 24-hour soak with no stale breach and no temporary Codex monitor
   intervention.
10. Remove GitHub scheduled triggers only after the private runner completes
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
