-- 001_create_enums.sql
-- Create PostgreSQL enums for the metric ontology system
-- See ADR-0002 for rationale

-- What is being measured?
DO $$
BEGIN
    CREATE TYPE metric_family_enum AS ENUM (
        'TIME_TO_PROVIDER',
        'TOTAL_LOS',
        'STRETCHER_OCCUPANCY'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

-- When does the clock start?
DO $$
BEGIN
    CREATE TYPE start_event_enum AS ENUM (
        'TRIAGE',
        'REGISTRATION',
        'DOOR',
        'UNKNOWN'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

-- When does the clock stop?
DO $$
BEGIN
    CREATE TYPE end_event_enum AS ENUM (
        'PHYSICIAN',
        'PROVIDER',
        'DISCHARGE',
        'FIRST_ASSESSMENT'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

-- How is the value calculated?
DO $$
BEGIN
    CREATE TYPE statistic_type_enum AS ENUM (
        'P90',
        'MEDIAN',
        'MEAN',
        'ROLLING_AVG',
        'ALGORITHMIC',
        'POINT_ESTIMATE'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

-- Which patients are included?
DO $$
BEGIN
    CREATE TYPE patient_scope_enum AS ENUM (
        'ALL',
        'MID_ACUITY',
        'NON_PRIORITY',
        'HIGH_ACUITY'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

-- Scraper health status
DO $$
BEGIN
    CREATE TYPE scraper_status_enum AS ENUM (
        'healthy',
        'error',
        'stale'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

-- Rollback:
-- DROP TYPE IF EXISTS scraper_status_enum;
-- DROP TYPE IF EXISTS patient_scope_enum;
-- DROP TYPE IF EXISTS statistic_type_enum;
-- DROP TYPE IF EXISTS end_event_enum;
-- DROP TYPE IF EXISTS start_event_enum;
-- DROP TYPE IF EXISTS metric_family_enum;
