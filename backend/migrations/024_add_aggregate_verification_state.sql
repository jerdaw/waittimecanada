-- Keep pre-gap aggregates from appearing verified when the new gap table is empty.

ALTER TABLE measurement_aggregates
    ADD COLUMN verification_state TEXT NOT NULL DEFAULT 'legacy_unverified'
        CHECK (verification_state IN ('legacy_unverified', 'verified')),
    ADD COLUMN verified_at TIMESTAMPTZ,
    ADD CONSTRAINT measurement_aggregate_verification_state_check CHECK (
        (verification_state = 'legacy_unverified' AND verified_at IS NULL)
        OR (verification_state = 'verified' AND verified_at IS NOT NULL)
    );

CREATE OR REPLACE VIEW measurement_aggregates_usable AS
SELECT aggregate.*
FROM measurement_aggregates AS aggregate
WHERE aggregate.verification_state = 'verified'
  AND NOT EXISTS (
      SELECT 1
      FROM measurement_aggregate_gaps AS gap
      WHERE gap.hospital_id = aggregate.hospital_id
        AND gap.period_type = aggregate.period_type
        AND gap.period_start = aggregate.period_start
        AND gap.metric_family = aggregate.metric_family
        AND gap.state = 'open'
  );

-- Rollback:
-- DROP VIEW IF EXISTS measurement_aggregates_usable;
-- ALTER TABLE measurement_aggregates
--     DROP CONSTRAINT measurement_aggregate_verification_state_check,
--     DROP COLUMN verified_at,
--     DROP COLUMN verification_state;
-- CREATE VIEW measurement_aggregates_usable AS
-- SELECT aggregate.*
-- FROM measurement_aggregates AS aggregate
-- WHERE NOT EXISTS (
--     SELECT 1
--     FROM measurement_aggregate_gaps AS gap
--     WHERE gap.hospital_id = aggregate.hospital_id
--       AND gap.period_type = aggregate.period_type
--       AND gap.period_start = aggregate.period_start
--       AND gap.metric_family = aggregate.metric_family
--       AND gap.state = 'open'
-- );
