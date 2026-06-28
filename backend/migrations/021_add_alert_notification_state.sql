-- 021_add_alert_notification_state.sql
-- Record whether an active incident actually produced an operator notification.

ALTER TABLE scraper_alert_state
    ADD COLUMN IF NOT EXISTS active_incident_notified_tier TEXT
        CHECK (active_incident_notified_tier IS NULL OR active_incident_notified_tier ~ '^P[0-3]$'),
    ADD COLUMN IF NOT EXISTS active_incident_notified_at TIMESTAMPTZ;

ALTER TABLE public_health_source_alert_state
    ADD COLUMN IF NOT EXISTS active_incident_notified_tier TEXT
        CHECK (active_incident_notified_tier IS NULL OR active_incident_notified_tier ~ '^P[0-3]$'),
    ADD COLUMN IF NOT EXISTS active_incident_notified_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_scraper_alert_state_notified_tier
    ON scraper_alert_state(active_incident_notified_tier)
    WHERE active_incident_notified_tier IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_public_health_source_alert_state_notified_tier
    ON public_health_source_alert_state(active_incident_notified_tier)
    WHERE active_incident_notified_tier IS NOT NULL;

-- Rollback:
-- DROP INDEX IF EXISTS idx_public_health_source_alert_state_notified_tier;
-- DROP INDEX IF EXISTS idx_scraper_alert_state_notified_tier;
-- ALTER TABLE public_health_source_alert_state
--     DROP COLUMN IF EXISTS active_incident_notified_at,
--     DROP COLUMN IF EXISTS active_incident_notified_tier;
-- ALTER TABLE scraper_alert_state
--     DROP COLUMN IF EXISTS active_incident_notified_at,
--     DROP COLUMN IF EXISTS active_incident_notified_tier;
