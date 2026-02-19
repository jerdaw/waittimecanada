-- 013_add_scraper_observability_columns.sql
-- Add structured observability metadata to scraper_status for
-- last-known-good and classified failure visibility.

ALTER TABLE scraper_status
    ADD COLUMN IF NOT EXISTS last_success_run TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_success_measurements_count INTEGER,
    ADD COLUMN IF NOT EXISTS last_error_run TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_error_category TEXT,
    ADD COLUMN IF NOT EXISTS last_error_stage TEXT,
    ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_run_duration_ms INTEGER;

CREATE INDEX IF NOT EXISTS idx_scraper_status_last_success_run
    ON scraper_status(last_success_run DESC);

CREATE INDEX IF NOT EXISTS idx_scraper_status_last_error_run
    ON scraper_status(last_error_run DESC);

CREATE INDEX IF NOT EXISTS idx_scraper_status_consecutive_failures
    ON scraper_status(consecutive_failures DESC);

-- Rollback:
-- ALTER TABLE scraper_status
--     DROP COLUMN IF EXISTS last_run_duration_ms,
--     DROP COLUMN IF EXISTS consecutive_failures,
--     DROP COLUMN IF EXISTS last_error_stage,
--     DROP COLUMN IF EXISTS last_error_category,
--     DROP COLUMN IF EXISTS last_error_run,
--     DROP COLUMN IF EXISTS last_success_measurements_count,
--     DROP COLUMN IF EXISTS last_success_run;
--
-- DROP INDEX IF EXISTS idx_scraper_status_consecutive_failures;
-- DROP INDEX IF EXISTS idx_scraper_status_last_error_run;
-- DROP INDEX IF EXISTS idx_scraper_status_last_success_run;
