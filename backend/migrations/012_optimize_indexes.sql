-- 012_optimize_indexes.sql
-- Add composite indexes to optimize common API query patterns.
--
-- 1. idx_measurements_hospital_metric_time:
--    Optimizes the "latest wait time" subquery in GET /api/hospitals
--    WHERE hospital_id = ? AND metric_family = 'TIME_TO_PROVIDER' ORDER BY timestamp_utc DESC
--
-- 2. idx_hospitals_province_verified:
--    Optimizes the main filter in GET /api/hospitals and GET /api/analytics/trends
--    WHERE province = ? AND is_visible = true AND is_verified = true

CREATE INDEX IF NOT EXISTS idx_measurements_hospital_metric_time
    ON measurements(hospital_id, metric_family, timestamp_utc DESC);

CREATE INDEX IF NOT EXISTS idx_hospitals_province_verified
    ON hospitals(province) WHERE is_visible = true AND is_verified = true;

-- Rollback:
-- DROP INDEX IF EXISTS idx_measurements_hospital_metric_time;
-- DROP INDEX IF EXISTS idx_hospitals_province_verified;
