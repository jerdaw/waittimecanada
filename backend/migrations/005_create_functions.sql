-- 005_create_functions.sql
-- Database functions for common operations
-- Depends on: 002_create_tables.sql

-- Function to check if two measurements are comparable
CREATE OR REPLACE FUNCTION are_measurements_comparable(
    measurement_a_id BIGINT,
    measurement_b_id BIGINT
) RETURNS BOOLEAN AS $$
DECLARE
    a measurements%ROWTYPE;
    b measurements%ROWTYPE;
BEGIN
    SELECT * INTO a FROM measurements WHERE id = measurement_a_id;
    SELECT * INTO b FROM measurements WHERE id = measurement_b_id;

    IF a IS NULL OR b IS NULL THEN
        RETURN FALSE;
    END IF;

    RETURN (
        a.metric_family = b.metric_family AND
        a.start_event = b.start_event AND
        a.end_event = b.end_event AND
        a.statistic_type = b.statistic_type
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get latest measurement for a hospital
CREATE OR REPLACE FUNCTION get_latest_measurement(
    p_hospital_id TEXT
) RETURNS measurements AS $$
    SELECT *
    FROM measurements
    WHERE hospital_id = p_hospital_id
    ORDER BY timestamp_utc DESC
    LIMIT 1;
$$ LANGUAGE sql STABLE;

-- Function to update scraper heartbeat
CREATE OR REPLACE FUNCTION update_scraper_heartbeat(
    p_source_id TEXT,
    p_status scraper_status_enum DEFAULT 'healthy',
    p_error_message TEXT DEFAULT NULL,
    p_measurements_count INTEGER DEFAULT 0
) RETURNS scraper_status AS $$
    INSERT INTO scraper_status (source_id, last_run, status, error_message, measurements_count)
    VALUES (p_source_id, NOW(), p_status, p_error_message, p_measurements_count)
    ON CONFLICT (source_id) DO UPDATE SET
        last_run = NOW(),
        status = p_status,
        error_message = p_error_message,
        measurements_count = p_measurements_count,
        updated_at = NOW()
    RETURNING *;
$$ LANGUAGE sql;

-- Function to check for stale scrapers (no update in 60 minutes)
CREATE OR REPLACE FUNCTION get_stale_scrapers(
    threshold_minutes INTEGER DEFAULT 60
) RETURNS SETOF scraper_status AS $$
    SELECT *
    FROM scraper_status
    WHERE last_run < NOW() - (threshold_minutes || ' minutes')::INTERVAL
    OR status = 'error';
$$ LANGUAGE sql STABLE;

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to tables
CREATE TRIGGER sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER hospitals_updated_at
    BEFORE UPDATE ON hospitals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER scraper_status_updated_at
    BEFORE UPDATE ON scraper_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Rollback:
-- DROP TRIGGER IF EXISTS scraper_status_updated_at ON scraper_status;
-- DROP TRIGGER IF EXISTS hospitals_updated_at ON hospitals;
-- DROP TRIGGER IF EXISTS sources_updated_at ON sources;
-- DROP FUNCTION IF EXISTS update_updated_at();
-- DROP FUNCTION IF EXISTS get_stale_scrapers(INTEGER);
-- DROP FUNCTION IF EXISTS update_scraper_heartbeat(TEXT, scraper_status_enum, TEXT, INTEGER);
-- DROP FUNCTION IF EXISTS get_latest_measurement(TEXT);
-- DROP FUNCTION IF EXISTS are_measurements_comparable(BIGINT, BIGINT);
