-- 015_add_metric_family_to_aggregates.sql
-- Allow multiple aggregations for the same hospital/period if they represent
-- different metric families (e.g. wait times vs occupancy).

ALTER TABLE measurement_aggregates
DROP CONSTRAINT IF EXISTS measurement_aggregates_hospital_id_period_type_period_start_key;

ALTER TABLE measurement_aggregates
ADD CONSTRAINT measurement_aggregates_unique_period_family
UNIQUE (hospital_id, period_type, period_start, metric_family);

-- Rollback:
-- ALTER TABLE measurement_aggregates DROP CONSTRAINT IF EXISTS measurement_aggregates_unique_period_family;
-- ALTER TABLE measurement_aggregates ADD UNIQUE (hospital_id, period_type, period_start);
