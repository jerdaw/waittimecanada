-- 010_create_regions_tables.sql
-- Create province region mapping tables for analytics segmentation.
-- Depends on: 002_create_tables.sql (hospitals)

CREATE TABLE IF NOT EXISTS regions (
    id TEXT PRIMARY KEY,
    province TEXT NOT NULL CHECK (char_length(province) = 2),
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (province, code),
    UNIQUE (province, name)
);

CREATE TABLE IF NOT EXISTS hospital_regions (
    region_id TEXT NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (region_id, hospital_id),
    UNIQUE (hospital_id)
);

CREATE INDEX IF NOT EXISTS idx_regions_province_sort
    ON regions (province, sort_order, name);

CREATE INDEX IF NOT EXISTS idx_hospital_regions_region
    ON hospital_regions (region_id);

-- Rollback:
-- DROP TABLE IF EXISTS hospital_regions;
-- DROP TABLE IF EXISTS regions;
