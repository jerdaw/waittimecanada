# Scraper Scheduling and Source Freshness

Wait Time Canada collects public emergency department wait-time data from four
provincial source families. This page documents the public behavior of that
collection layer without exposing production runbooks or private monitoring
configuration.

## Source Families

| Province | Source ID | Parser Approach | Methodology Tagging |
|----------|-----------|-----------------|---------------------|
| Quebec | `quebec-msss` | HTML parsing | `REGISTRATION -> PHYSICIAN`, rolling average; occupancy where published |
| Ontario | `ontario-health` | HTTP + HTML table parsing | `TRIAGE -> PHYSICIAN`, mean |
| Alberta | `alberta-ahs` | Browser-rendered page parsing | `TRIAGE -> PHYSICIAN`, point estimate |
| British Columbia | `bc-phsa` | HTML + JSON extraction | `TRIAGE -> PHYSICIAN`, P90 |

## Freshness Model

- Each scraper writes a status record after a collection attempt.
- Public API and dashboard surfaces use status records to communicate freshness
  and source-health state.
- Source-health checks should be state-change aware so repeated unresolved
  failures do not create duplicate notifications.
- Source freshness is a data-quality signal, not a guarantee that upstream
  provincial data is current or complete.

## Local Commands

```bash
cd backend
uv sync --locked --no-dev

uv run python -m waittime.cli.scraper --all --dry-run
uv run python -m waittime.cli.scraper --source ontario-health --dry-run
uv run python -m waittime.cli.check_heartbeat --dry-run --verbose
```

## Interpretation Limits

- Provincial sources can change methodology or page structure without notice.
- The platform preserves source semantics and should not normalize incompatible
  metrics into false direct comparisons.
- Public wait-time data can lag real operational conditions.
- This project is not a medical advice, triage, or hospital-recommendation
  service.

## Public Documentation Boundary

This repository contains public project documentation and reproducible
development information. Deployment details, credentials, monitoring
configuration, private operational notes, and environment-specific production
paths are intentionally excluded from public documentation.
