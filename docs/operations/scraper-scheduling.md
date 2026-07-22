# Scraper Scheduling and Source Freshness

Wait Time Canada checks four provincial public sources for updates. This page
describes the repository-backed public contract; deployment credentials and
private operational procedures remain outside this repository.

## Verified Production Cadence

| Layer                       | Repository configuration                                     | Public meaning                                                                           |
| --------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Provincial scraper workflow | `29 * * * *` in `.github/workflows/scraper-cron.yml`         | GitHub is asked to start one check each hour at minute 29                                |
| Heartbeat monitor           | `14,44 * * * *` in `.github/workflows/heartbeat-monitor.yml` | Source status is checked twice hourly; stale state can dispatch a recovery scrape        |
| Manual recovery             | `workflow_dispatch`                                          | An operator can request a source check when scheduled execution is delayed or missed     |
| Trusted-runner pilot        | hourly scrape at minute 17; watchdog at minutes 07 and 37    | A documented alternative target, not proof that a particular production runner is active |

“Hourly” describes the configured check interval. GitHub scheduled workflows can
start late or occasionally be skipped, scrapers take time to run, and provincial
publishers update on their own schedules. The site therefore says **Sources
Checked Hourly**, never “fresh every hour” or “real-time.”

## What One Collection Run Does

The `--all` command processes Alberta, British Columbia, Ontario, and Quebec in
sequence. Each source fetches and parses its upstream data, writes measurements,
and then writes its own heartbeat. A visitor can consequently observe a mixed
snapshot while a run is in progress: earlier sources may have new timestamps
while later sources still show their previous successful run.

The collection client retries a failed request up to three times with bounded
exponential backoff. HTTP connections use finite timeouts; Ontario has a longer
fallback read path, and Quebec may paginate through multiple result pages. The
workflow job is capped at 35 minutes. A run can be considered partially useful
when at least one source produced data, while the heartbeat monitor still
identifies stale or failed sources individually.

## Provincial Publication Timing

| Province         | Public source                                                                                                                                                                                   | Publisher timing documented by the source                                                         | Platform interpretation                                             |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Alberta          | [AHS estimated emergency wait times](https://www.albertahealthservices.ca/waittimes/Page14230.aspx)                                                                                             | The public display reports frequent updates, approximately every two minutes                      | The platform samples the latest value available when its check runs |
| British Columbia | [ED Wait Times methodology](https://www.edwaittimes.ca/about)                                                                                                                                   | The publisher describes five-minute updates                                                       | The platform samples the latest published value hourly              |
| Ontario          | [Ontario Health time spent in emergency departments](https://www.ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments)                                             | The public indicator is a periodic reporting product rather than a live feed                      | An hourly check does not make the underlying indicator hourly       |
| Quebec           | [Quebec emergency-room situation](https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec) | The province republishes values during the day without a stable interval promised by this project | The platform preserves the upstream timestamp and exposes staleness |

Publisher timing can change without notice. The provincial pages are the
authoritative source for their current publication methods.

## Database, API, Cache, and Browser Timing

A successful scraper writes measurements and a `scraper_status` heartbeat per
source. Public surfaces then add bounded read delay:

- `/api/health` uses a 60-second in-process read cache and returns `no-store` to
  clients. Its default public stale threshold is 120 minutes.
- `/api/hospitals`, `/api/status`, and aggregate `/api/data-quality` use a
  five-minute in-process cache and five-minute shared-cache response window,
  with a 15-minute stale-while-revalidate allowance.
- The homepage server-renders a database-derived coverage snapshot. While the
  tab is visible, the browser requests the selected province and national
  coverage again every five minutes and immediately after the tab becomes
  visible.
- `SystemStatus` and the status page poll their health surfaces every five
  minutes while visible.

These layers mean a newly written measurement may take several minutes to
appear in a browser. Timestamps, stale indicators, and per-source status are the
truth-bearing signals; a check schedule is not a delivery guarantee.

## Current Freshness Versus 24-Hour Completeness

`GET /api/health` and `GET /api/status` answer different questions:

- `/api/health.healthy` describes current database connectivity and source
  heartbeat freshness against the 120-minute threshold.
- `/api/status.overall_status` grades the average proportion of the previous 24
  distinct UTC measurement hours present across active sources. Its explicit
  basis is `measurement_hour_completeness_24h`.

These values are not contradictory. At `2026-07-22T02:24:54Z`, all four source
heartbeats were healthy and about 88 minutes old, while each source had 11 of 24
expected measurement hours. `/api/health` was therefore healthy and
`/api/status` was critical at `0.458`. Recent workflow history contained
successful but irregularly spaced scheduled runs, supporting missed or delayed
collection windows rather than a calculation error.

## Public Coverage Counts

The homepage count is derived from verified, visible hospital rows at request
time. It is server-rendered for the first response and returned as `coverage` by
`GET /api/hospitals`, including `hospital_count`, `province_count`,
`generated_at`, and `latest_measurement_at`. The UI does not use a static
“plus” label and does not substitute a province-filtered list length for the
national count. When coverage cannot be queried, it shows an explicit
unavailable state rather than an ellipsis or invented total.

## Freshness Vocabulary

Use these terms consistently:

- **Checked hourly:** the configured scheduler asks the platform to inspect each
  provincial source once per hour.
- **Last updated:** the timestamp attached to the latest stored measurement.
- **Stale:** a source heartbeat has crossed the public 120-minute threshold.
- **Failed:** the latest collection attempt recorded an error state.
- **Unavailable:** the application could not obtain enough evidence to state a
  value or count.

Do not describe the service as real-time, continuously updated, guaranteed
hourly, or fresh every four hours.

## Local Verification

```bash
cd backend
uv sync --locked --no-dev

uv run python -m waittime.cli.scraper --all --dry-run
uv run python -m waittime.cli.check_heartbeat --dry-run --verbose
cd ..
python3 scripts/check-scraper-workflow.py
```

The trusted-runner wrapper remains available for a separately configured runner:

```bash
python3 scripts/waittime-freshness-runner.py check
python3 scripts/waittime-freshness-runner.py watchdog --dry-run
python3 scripts/waittime-freshness-runner.py scrape
python3 scripts/waittime-freshness-runner.py aggregate
python3 scripts/waittime-freshness-runner.py smoke
```

Its watchdog treats age 90 minutes or greater as unsafe so recovery can begin
before the public 120-minute stale threshold is crossed.

## Interpretation Limits

- Provincial sources can change methodology or page structure without notice.
- The platform preserves source semantics and does not normalize incompatible
  metrics into false direct comparisons.
- Public wait-time data can lag real operational conditions.
- This project is not a medical advice, triage, or hospital-recommendation
  service.
