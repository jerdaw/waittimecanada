# GitHub Collector Dispatcher Preparation

**Status:** Inert preparation only. The example service is dry-run-only, the
execution gate is off by default, and no timer is installed or enabled by this
repository.

This helper is a narrowly scoped option for requesting the existing
`scraper-cron.yml` workflow on `main`. It is not a deployment runner, a data
quality check, or proof that any scheduled run stored measurements.

## Guarded Request

The helper considers only the current hourly slot during `:39` through `:43`
UTC, for the GitHub scheduled run at `:29` in that same hour. It does not catch
up missed slots. Before requesting a run, it checks for recent scheduled or
manual-dispatch runs for that slot and for target-workflow runs in the queued,
in-progress, requested, waiting, or pending states. The recent-run check is
bounded to 1,000 records and must have consistent page counts; an incomplete or
unavailable check prevents a request.

The default invocation is a dry run and performs no API or state-file I/O. An
actual request requires both the explicit `--execute` flag and
`WTC_GITHUB_DISPATCH_ENABLED=1`, plus a `GITHUB_TOKEN` available to the
process. The token is sent only to the fixed GitHub API host, and neither the
token nor raw API responses are printed or saved. The request targets `main`,
sets `refresh_analytics` to `false`, and asks GitHub to return the created run
ID.

The dispatcher uses a host-local nonblocking lock and an atomic, fsynced ledger
at `/var/lib/waittimecanada-dispatcher/dispatch-ledger.json`. It records a
slot as `in_flight` durably before making the POST. A valid HTTP 200 response
with a positive run ID changes the slot to `accepted`; any transport failure,
non-200 response, or malformed receipt leaves it `ambiguous` (or `in_flight`
if recording ambiguity fails). If local receipt persistence fails, it remains
non-retryable as `in_flight` or `accepted`. A restart will not POST again for
that slot. This is a no-retry-per-slot rule, not a broader service halt; the
next eligible hourly slot is evaluated independently. An ambiguous result
requires separate reconciliation and must not be cleared to force a retry.

## Limits and Integration Boundary

The local lock cannot coordinate with GitHub's scheduled workflow or its
heartbeat recovery workflow. A delayed scheduled run or heartbeat-triggered
dispatch can race the preflight check. The `:39`–`:43` window reduces direct
overlap with the known `:44` heartbeat schedule but cannot eliminate that
cross-system race. The helper does not provide exactly-once dispatch,
guaranteed hourly coverage, or evidence of collection completeness.

The service and timer files under `examples/` are copy/adapt references only;
they remain dry-run-only and have no enablement section. Any later host-side
integration must go through that host's owning repository and managed
configuration authority. A separate activation decision must re-confirm the
target workflow and schedule, assign a single state owner and durable ledger
location, and arrange a least-privilege repository-scoped Actions credential
through the host's managed secret mechanism. This WTC repository does not
provision credentials, install a timer, or activate the dispatcher.
