-- 014_relax_value_constraint.sql
-- Relax the strictly positive constraint on measurement values to allow zero.
-- This is necessary for 0% occupancy (STRETCHER_OCCUPANCY) and occasional 0-min wait times.
-- Depends on: 002_create_tables.sql

ALTER TABLE measurements
DROP CONSTRAINT measurements_value_check;

ALTER TABLE measurements
ADD CONSTRAINT measurements_value_check CHECK (value >= 0);

COMMENT ON COLUMN measurements.value IS 'The measured value in minutes or percentage. Relaxed to >= 0 to support occupancy metrics.';
