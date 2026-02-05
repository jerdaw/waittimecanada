# ADR-0006: Dead Man's Switch Scraper Monitoring

**Status:** Accepted
**Date:** 2026-02-05
**Deciders:** Development Team
**Related:** M12 Phase 2 - Research Infrastructure

---

## Context

Scrapers running on scheduled GitHub Actions can fail silently due to:
- API changes at data sources (Ontario Health, Quebec MSSS)
- Network issues
- Rate limiting
- Authentication problems
- Database connection failures

Silent failures mean users see stale data without knowing it, undermining the project's credibility and defeating the purpose of a "Health Systems Observatory."

**The Problem:** How do we ensure scraper failures are detected and reported quickly?

---

## Decision

We implemented a **Dead Man's Switch** monitoring system with multiple layers:

### 1. **Backend: Heartbeat Tracking**
- Every scraper run writes to `scraper_status` table with timestamp
- `AlertService` sends Pushover notifications for stale/error states
- `check_heartbeat` CLI command queries database and triggers alerts
- Threshold: 60 minutes (scrapers run every 15 minutes, so 4x missed runs)

### 2. **GitHub Actions: Automated Monitoring**
- Workflow runs every 30 minutes (`heartbeat-monitor.yml`)
- Calls `check_heartbeat` CLI
- Sends Pushover alerts on failure
- Non-blocking: doesn't prevent scraper runs

### 3. **Frontend: User-Visible Status**
- `SystemStatus` component displays real-time health
- 3 states: Healthy (<60 min), Degraded (60-120 min), Down (>120 min)
- Polls `/api/health` endpoint every minute
- Shows time since last update
- Positioned in page footer

### 4. **API: Health Endpoint**
- `/api/health` aggregates status across all sources
- Returns overall health flag and per-source details
- Used by both SystemStatus component and external monitoring

---

## Architecture

```
┌─────────────────┐
│ Scraper Runs    │
│ (every 15 min)  │
└────────┬────────┘
         │ writes heartbeat
         ▼
┌─────────────────┐
│ scraper_status  │◄────┐
│ table           │     │ queries
└─────────────────┘     │
         │              │
         │ queries      │
         ▼              │
┌─────────────────┐     │
│ GitHub Action   │─────┘
│ (every 30 min)  │
└────────┬────────┘
         │ if stale
         ▼
┌─────────────────┐
│ Pushover API    │
│ (push notify)   │
└─────────────────┘

┌─────────────────┐
│ User Browser    │
└────────┬────────┘
         │ polls every 60s
         ▼
┌─────────────────┐
│ /api/health     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SystemStatus    │
│ Component       │
└─────────────────┘
```

---

## Rationale

### Why Pushover?
- **Simple API** - Single POST request, no OAuth complexity
- **Free tier** - Sufficient for personal projects
- **Mobile apps** - iOS/Android notifications
- **Reliable** - No email deliverability issues
- **Low latency** - Instant push vs email delays

**Alternatives Considered:**
- Email (SMTP) - Rejected: deliverability issues, spam filters, configuration complexity
- Slack webhooks - Rejected: requires workspace, overkill for solo project
- Twilio SMS - Rejected: costs money for every alert
- Discord webhooks - Rejected: not mobile-friendly

### Why 60-minute threshold?
- Scrapers run every 15 minutes (4 runs per hour)
- 60 minutes = 4 consecutive failures before alert
- Reduces noise from transient failures
- Still fast enough to detect real issues
- Users see "degraded" warning at 60 min, "down" at 120 min

### Why visible status indicator?
- **Transparency** - Users know if data is fresh
- **Trust building** - Shows we monitor our own system
- **Professional** - Demonstrates operational maturity
- **CanMEDS Leader** - Infrastructure thinking for portfolio

---

## Implementation Details

### AlertService (Pushover Integration)
```python
class AlertService:
    def alert_scraper_stale(self, source_id: str, age_minutes: int):
        """Alert when scraper hasn't run recently."""
        self.send_alert(
            title=f"⚠️ Scraper Stale: {source_id}",
            message=f"No heartbeat for {age_minutes} minutes.",
            priority=1,  # High priority
            url="https://github.com/jerdaw/waittimecanada/actions"
        )
```

### Frontend Health States
- **Healthy** (green): `age < 60 min && healthy == true`
- **Degraded** (amber): `age >= 60 min && age < 120 min`
- **Down** (red): `age >= 120 min || healthy == false`
- **Loading** (gray): Initial state before first check

### Graceful Degradation
- If Pushover credentials not configured: logs to console, doesn't fail
- If database unavailable: health endpoint returns 500 but frontend shows "down"
- If GitHub Actions fails: doesn't block scraper runs

---

## Consequences

### Positive
✅ **Early Detection** - Failures detected within 60 minutes
✅ **Zero Cost** - Pushover free tier, GitHub Actions free
✅ **User Transparency** - Status visible without hunting for it
✅ **Professional Image** - Shows operational maturity
✅ **Admissions Value** - Demonstrates Leader competency
✅ **Debugging Aid** - Health endpoint useful for troubleshooting

### Negative
⚠️ **External Dependency** - Relies on Pushover API
⚠️ **Manual Setup** - Requires creating Pushover account and adding secrets
⚠️ **Noise Risk** - Could generate false alarms if threshold too low
⚠️ **Privacy** - Health data is public (but contains no sensitive info)

### Neutral
🔵 **Not Real-Time** - 30-minute check interval (acceptable trade-off)
🔵 **Single Point of Failure** - If database down, all monitoring stops (but database is also required for app)

---

## Alternatives Not Chosen

### 1. **No Monitoring**
- Rejected: Silent failures undermine credibility
- Risk: Users complain about stale data, lose trust

### 2. **Manual Checks**
- Rejected: Not scalable, requires daily vigilance
- Risk: Failures go unnoticed for days

### 3. **Only Backend Monitoring (No Frontend Indicator)**
- Rejected: Users deserve transparency
- Missed opportunity: Professional image for portfolio

### 4. **Real-Time WebSocket Status**
- Rejected: Over-engineered for current scale
- Unnecessary: 1-minute polling sufficient
- Could revisit if needed for production at scale

---

## Testing Strategy

### Backend Tests
- AlertService sends notifications correctly
- Graceful degradation when credentials missing
- check_heartbeat CLI exits with correct codes

### Frontend Tests (7 tests)
- Renders all 4 status states correctly
- Calculates age correctly
- Polls health endpoint every minute
- Shows time since last update
- Accessible (ARIA attributes)
- Handles network errors gracefully

### Manual Testing
1. Create Pushover account and test alert delivery
2. Verify GitHub Action runs and checks heartbeat
3. Confirm frontend status updates in real-time
4. Test degraded/down states by stopping scrapers

---

## Future Considerations

### Potential Enhancements
- **Multi-Channel Alerts** - Add email/SMS as fallback
- **Alert Deduplication** - Don't spam if issue persists
- **Recovery Notifications** - Alert when scraper recovers
- **Status Page** - Dedicated `/status` page with history
- **Metrics Dashboard** - Uptime percentage, MTTR tracking
- **SLA Tracking** - Document target availability (e.g., 99% uptime)

### Production Requirements (Not Yet Implemented)
- Configure Pushover in production environment
- Set up monitoring for the monitoring (meta-monitoring)
- Document runbook for responding to alerts
- Consider adding PagerDuty for critical issues

---

## Related Documents

- Implementation Plan: `docs/planning/implementation/milestone-12-research.md`
- Manual Setup: `docs/planning/manual-tasks.md` (Pushover configuration)
- API Documentation: `docs/API.md` (health endpoint)

---

## Success Metrics

**Operational:**
- Alert delivery latency < 5 minutes
- False positive rate < 5%
- Detection of 100% of scraper failures

**Portfolio:**
- Demonstrates "Leader" CanMEDS competency
- Shows understanding of production operations
- Evidence of professional software practices

---

**Last Updated:** 2026-02-05
**Review Date:** After production deployment
