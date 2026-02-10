-- 011_add_occupancy_columns.sql
-- Add occupancy metrics to measurements table
-- Depends on: 002_create_tables.sql

ALTER TABLE measurements
ADD COLUMN patients_waiting INTEGER CHECK (patients_waiting >= 0),
ADD COLUMN patients_in_treatment INTEGER CHECK (patients_in_treatment >= 0),
ADD COLUMN total_treatment_spaces INTEGER CHECK (total_treatment_spaces >= 0);

COMMENT ON COLUMN measurements.patients_waiting IS 'Number of patients currently waiting for a provider';
COMMENT ON COLUMN measurements.patients_in_treatment IS 'Number of patients currently being treated';
COMMENT ON COLUMN measurements.total_treatment_spaces IS 'Total capacity of the ER (for utilization calc)';
