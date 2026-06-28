# 0028. Critical-Only Operational Notification Mode

Date: 2026-06-27

## Status

Accepted

## Context

State-change-aware alerting already prevents repeated notifications for the
same unresolved scraper or public-health ingest incident. During cost-control
and solo-maintainer periods, the project also needs a way to preserve incident
state without paging on every P2/P3 operational degradation.

The repository must keep public source-freshness signals accurate while
avoiding private monitoring details, credentials, or provider-specific routing
rules in public docs.

## Decision

Add a critical-only operational notification mode controlled by
`OPERATIONAL_NOTIFICATION_MODE=critical_only`.

In critical-only mode:

- P0/P1 operational notifications are allowed.
- P2/P3 operational notifications are suppressed.
- Suppressed incidents are still persisted in alert-state tables.
- Recovery notifications are sent only when the active incident previously
  generated a critical notification.
- GitHub fallback workflows use the wider 720-minute / six-consecutive-failure
  heartbeat threshold while scheduled operational workflows remain constrained.

Migration `021_add_alert_notification_state.sql` records the notification tier
and timestamp associated with the current active scraper or public-health source
incident.

## Consequences

- Public freshness and data-quality reporting remain explicit.
- Operator paging volume is reduced during free-tier or solo-maintainer periods.
- Alert state can distinguish "incident exists" from "incident paged an
  operator."
- Private notification routing and escalation details remain outside this
  public repository.

## Related

- `docs/adr/0020-raw-retention-and-stateful-alerting.md`
- `docs/adr/0027-hybrid-ci-offload-strategy.md`
- `docs/operations/heartbeat-offload-pilot.md`
