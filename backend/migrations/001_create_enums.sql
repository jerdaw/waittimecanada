-- 001_create_enums.sql
-- Create PostgreSQL enums for the metric ontology system
-- See ADR-0002 for rationale

-- What is being measured?
DO $$ BEGIN
    CREATE TYPE metric_family_enum AS ENUM (
    'TIME_TO_PROVIDER',
    'TOTAL_LOS',
    'STRETCHER_OCCUPANCY'
);

-- When does the clock start?
CREATE TYPE start_event_enum AS ENUM (
    'TRIAGE',
    'REGISTRATION',
    'DOOR',
    'UNKNOWN'
);

-- When does the clock stop?
CREATE TYPE end_event_enum AS ENUM (
    'PHYSICIAN',
    'PROVIDER',
    'DISCHARGE',
    'FIRST_ASSESSMENT'
);

-- How is the value calculated?
CREATE TYPE statistic_type_enum AS ENUM (
    'P90',
    'MEDIAN',
    'MEAN',
    'ROLLING_AVG',
    'ALGORITHMIC',
    'POINT_ESTIMATE'
);

-- Which patients are included?
CREATE TYPE patient_scope_enum AS ENUM (
    'ALL',
    'MID_ACUITY',
    'NON_PRIORITY',
    'HIGH_ACUITY'
);

-- Scraper health status
CREATE TYPE scraper_status_enum AS ENUM (
    'healthy',
    'error',
    'stale'
);

-- Rollback:
-- DROP TYPE IF EXISTS scraper_status_enum;
-- DROP TYPE IF EXISTS patient_scope_enum;
-- DROP TYPE IF EXISTS statistic_type_enum;
-- DROP TYPE IF EXISTS end_event_enum;
-- DROP TYPE IF EXISTS start_event_enum;
-- DROP TYPE IF EXISTS metric_family_enum;
