-- Atomically preserve permanent summaries while ensuring only verified
-- aggregates without unresolved methodology gaps are served as current results.

CREATE TABLE measurement_aggregate_gaps (
    hospital_id TEXT NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    period_type TEXT NOT NULL CHECK (period_type IN ('hourly', 'daily', 'weekly', 'monthly')),
    period_start TIMESTAMPTZ NOT NULL,
    metric_family TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('open', 'resolved')),
    reason TEXT NOT NULL CHECK (
        reason IN ('ambiguous_methodology', 'unsupported_patient_scope')
    ),
    fingerprint TEXT NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
    signature_count INTEGER NOT NULL CHECK (signature_count > 0),
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    PRIMARY KEY (hospital_id, period_type, period_start, metric_family),
    CONSTRAINT measurement_aggregate_gap_resolution_state CHECK (
        (state = 'open' AND resolved_at IS NULL)
        OR (state = 'resolved' AND resolved_at IS NOT NULL)
    )
);

CREATE INDEX idx_measurement_aggregate_gaps_open
    ON measurement_aggregate_gaps (period_type, period_start)
    WHERE state = 'open';

ALTER TABLE measurement_aggregates
    ADD COLUMN verification_state TEXT NOT NULL DEFAULT 'legacy_unverified',
    ADD COLUMN verified_at TIMESTAMPTZ,
    ADD CONSTRAINT measurement_aggregates_verification_state_check CHECK (
        verification_state IN ('legacy_unverified', 'verified')
    ),
    ADD CONSTRAINT measurement_aggregate_verification_state_check CHECK (
        (verification_state = 'legacy_unverified' AND verified_at IS NULL)
        OR (verification_state = 'verified' AND verified_at IS NOT NULL)
    );

CREATE VIEW measurement_aggregates_usable AS
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
-- DROP TABLE IF EXISTS measurement_aggregate_gaps;
-- ALTER TABLE measurement_aggregates
--     DROP CONSTRAINT IF EXISTS measurement_aggregate_verification_state_check,
--     DROP CONSTRAINT IF EXISTS measurement_aggregates_verification_state_check,
--     DROP COLUMN IF EXISTS verified_at,
--     DROP COLUMN IF EXISTS verification_state;
