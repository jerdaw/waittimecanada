-- 017_add_scraper_alert_state.sql
-- Persist scraper alert incidents so heartbeat checks only notify on state changes.

CREATE TABLE IF NOT EXISTS scraper_alert_state (
    source_id TEXT PRIMARY KEY REFERENCES sources(id),
    active_incident_kind TEXT CHECK (
        active_incident_kind IS NULL OR active_incident_kind IN ('stale', 'error')
    ),
    active_incident_fingerprint TEXT,
    opened_at TIMESTAMPTZ,
    last_notified_at TIMESTAMPTZ,
    last_resolved_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraper_alert_state_active_incident
    ON scraper_alert_state(active_incident_kind)
    WHERE active_incident_kind IS NOT NULL;

-- Rollback:
-- DROP INDEX IF EXISTS idx_scraper_alert_state_active_incident;
-- DROP TABLE IF EXISTS scraper_alert_state;
