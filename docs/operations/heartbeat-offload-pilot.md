# Heartbeat Offload Pilot

This guide is the public, repo-side contract for the first ADR-0027 offload
pilot. It documents how a trusted non-GitHub runner should invoke the existing
heartbeat checker without exposing private infrastructure, credentials, or
monitoring configuration.

This is not a private deployment runbook. Runner registration, secret values,
alert routing, private log retention, and service scheduling belong in the
private/shared operations source of truth.

## Command Contract

Run the same heartbeat checker used by the GitHub manual fallback workflow:

```bash
cd backend
uv run python -m waittime.cli.check_heartbeat --max-age 120 --max-consecutive-failures 1
```

The backend package must be installed in the runner environment before the
command runs:

```bash
cd backend
python -m pip install "uv==0.11.23"
uv sync --locked --no-dev
```

Required environment variable names:

- `DATABASE_URL`

Optional alert environment variable names:

- `ALERT_API_URL`
- `ALERT_USER_KEY`
- `ALERT_API_TOKEN`

Do not print environment values, connection strings, tokens, webhook URLs, or
private runner details in logs.

## Exit Codes

- `0`: all checked scraper heartbeats are healthy.
- Non-zero: at least one source is stale, at least one source has crossed the
  consecutive-failure threshold, or the command failed before completing.

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
  `.github/workflows/heartbeat-monitor.yml` as the fallback entry point until
  the offloaded job has completed one normal operating cycle.
- Keep public summaries concise and free of private paths, private hostnames,
  tokens, database URLs, and alert-route details.

## Pilot Checklist

1. Provision the trusted runner outside this public repository.
2. Configure the required `DATABASE_URL` secret and optional alert secrets in
   the private runner environment.
3. Run a dry-run check first:

   ```bash
   cd backend
   python -m waittime.cli.check_heartbeat --max-age 120 --max-consecutive-failures 1 --dry-run --verbose
   ```

4. Confirm dry-run logs contain no secret values, private paths, private
   hostnames, tokens, database URLs, or alert-route details.
5. Run one real heartbeat check manually with the command contract above.
6. Compare the output and exit code with the GitHub manual fallback workflow.
7. Enable a private schedule only after the manual offloaded run behaves as
   expected.
8. Keep the GitHub manual fallback available until the offloaded schedule has
   completed one normal operating cycle.

## Copy/Adapt Example

A copy/adapt Forgejo-style example is available at
[examples/forgejo-heartbeat-monitor.yml](examples/forgejo-heartbeat-monitor.yml).
It is intentionally stored under `docs/operations/examples/`, not under
`.forgejo/workflows/`, so merging this repository change cannot start a private
runner job.

If the private runner uses a self-hosted GitHub runner instead of Forgejo
Actions, keep the same command contract and safety rules.

## Related Documents

- [ADR-0027: Hybrid CI Offload Strategy](../adr/0027-hybrid-ci-offload-strategy.md)
- [Scraper Scheduling and Source Freshness](scraper-scheduling.md)
- [Manual Tasks](../planning/manual-tasks.md)
