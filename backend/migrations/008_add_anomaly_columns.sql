-- 008_add_anomaly_columns.sql
-- Add anomaly detection columns to the measurements table.
-- Depends on: 002_create_tables.sql (measurements)
--
-- Anomalies are flagged but NOT excluded from display or export.
-- The flag is metadata that enables transparency about data quality.

ALTER TABLE measurements
ADD COLUMN IF NOT EXISTS is_anomaly BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE measurements
ADD COLUMN IF NOT EXISTS anomaly_reason TEXT;

-- Index for querying anomalies (used by anomaly feed and data quality page)
CREATE INDEX IF NOT EXISTS idx_measurements_anomaly
    ON measurements (is_anomaly, timestamp_utc DESC)
    WHERE is_anomaly = TRUE;

-- Rollback:
-- ALTER TABLE measurements DROP COLUMN IF EXISTS anomaly_reason;
-- ALTER TABLE measurements DROP COLUMN IF EXISTS is_anomaly;
-- DROP INDEX IF EXISTS idx_measurements_anomaly;
