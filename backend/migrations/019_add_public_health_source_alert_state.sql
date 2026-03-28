-- 019_add_public_health_source_alert_state.sql
-- Persist public-health-hub ingest incidents so hard-fail source alerting is state-change driven.

CREATE TABLE IF NOT EXISTS public_health_source_alert_state (
    source_id TEXT PRIMARY KEY REFERENCES public_data_sources(source_id),
    active_incident_kind TEXT CHECK (
        active_incident_kind IS NULL OR active_incident_kind IN ('degraded')
    ),
    active_incident_fingerprint TEXT,
    opened_at TIMESTAMPTZ,
    last_notified_at TIMESTAMPTZ,
    last_resolved_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_public_health_source_alert_state_active_incident
    ON public_health_source_alert_state(active_incident_kind)
    WHERE active_incident_kind IS NOT NULL;

-- Rollback:
-- DROP INDEX IF EXISTS idx_public_health_source_alert_state_active_incident;
-- DROP TABLE IF EXISTS public_health_source_alert_state;
