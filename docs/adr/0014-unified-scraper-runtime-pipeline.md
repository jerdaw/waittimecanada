# ADR 0014: Unified Scraper Runtime Pipeline

## Status
Accepted (2026-02-08)

## Context
Scraper execution previously split persistence concerns across two paths:

1. Scraper internals (`BaseScraper.run`) for anomaly checks and heartbeat events when a DB handle exists.
2. CLI orchestration (`backend/src/waittime/cli/scraper.py`) for hospital upserts, measurement inserts, and heartbeat writes.

This duplication increased drift risk and made behavior harder to reason about under failure.

## Decision
Adopt a single authoritative runtime path by routing persistence through `BaseScraper.run(...)`:

1. CLI now instantiates scrapers with `db=DatabaseService()`.
2. CLI invokes `scraper.run(save_to_db=True, before_save=...)`.
3. `BaseScraper.run` retains anomaly checks, DB insert, and success/failure heartbeat recording.
4. A new optional `before_save(measurements)` hook in `BaseScraper.run` is used for hospital prerequisite upserts.

## Consequences

### Positive
- One execution path governs anomaly detection, inserts, and heartbeat semantics.
- Reduced duplicate error handling in CLI.
- Preserves prerequisite hospital upsert behavior without reintroducing split writes.

### Tradeoff
- `BaseScraper.run` surface area is slightly larger due to hook support.
- Hook callers must remain side-effect-safe and idempotent.

## Follow-Up
1. Keep heartbeat monitoring source discovery dynamic (`sources` table), not hardcoded.
2. Add integration coverage for end-to-end scraper run with DB fixtures when available.
