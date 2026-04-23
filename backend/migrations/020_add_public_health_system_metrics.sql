-- 020_add_public_health_system_metrics.sql
-- Storage lane for Ontario EMS/system-context metrics.

CREATE TABLE IF NOT EXISTS public_health_system_metrics (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES public_data_sources(source_id) ON DELETE CASCADE,
    series_key TEXT NOT NULL,
    province CHAR(2) NOT NULL,
    geography_type TEXT NOT NULL,
    geography_name TEXT NOT NULL,
    reporting_year INTEGER NOT NULL CHECK (reporting_year >= 1900 AND reporting_year <= 3000),
    dimension_label TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance_url TEXT NOT NULL,
    last_refreshed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_public_health_system_metrics_source_series_year
    ON public_health_system_metrics(source_id, series_key, reporting_year);

CREATE INDEX IF NOT EXISTS idx_public_health_system_metrics_geography_name
    ON public_health_system_metrics(geography_name);

-- Rollback:
-- DROP INDEX IF EXISTS idx_public_health_system_metrics_geography_name;
-- DROP INDEX IF EXISTS idx_public_health_system_metrics_source_series_year;
-- DROP TABLE IF EXISTS public_health_system_metrics;
