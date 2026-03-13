-- 016_add_measurement_retention_efficiency_guards.sql
-- Support indefinite raw-measurement retention with safer idempotency and lower-cost
-- time-range scans.
--
-- 1. Remove exact duplicate observations already present in measurements.
-- 2. Add a uniqueness guard so exact retries do not duplicate raw rows.
-- 3. Add a BRIN index on timestamp_utc for append-heavy historical range queries.

WITH ranked_measurements AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY
                hospital_id,
                timestamp_utc,
                metric_family,
                start_event,
                end_event,
                statistic_type,
                patient_scope,
                source_id,
                value,
                raw_payload_hash
            ORDER BY id
        ) AS duplicate_rank
    FROM measurements
),
duplicate_measurements AS (
    SELECT id
    FROM ranked_measurements
    WHERE duplicate_rank > 1
)
DELETE FROM measurements
WHERE id IN (SELECT id FROM duplicate_measurements);

ALTER TABLE measurements
ADD CONSTRAINT measurements_exact_observation_unique
UNIQUE (
    hospital_id,
    timestamp_utc,
    metric_family,
    start_event,
    end_event,
    statistic_type,
    patient_scope,
    source_id,
    value,
    raw_payload_hash
);

CREATE INDEX IF NOT EXISTS idx_measurements_timestamp_brin
    ON measurements USING BRIN (timestamp_utc);

-- Rollback:
-- DROP INDEX IF EXISTS idx_measurements_timestamp_brin;
-- ALTER TABLE measurements DROP CONSTRAINT IF EXISTS measurements_exact_observation_unique;
