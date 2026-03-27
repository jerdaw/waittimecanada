-- 018_create_public_health_hub_tables.sql
-- Foundation schema for the public-health-data-hub Batch A module.

CREATE TABLE IF NOT EXISTS public_data_sources (
    source_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL CHECK (
        domain IN (
            'provider_facility',
            'aed',
            'safety_alert',
            'health_product_reference',
            'environmental_overlay',
            'system_context'
        )
    ),
    source_name TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (
        scope IN ('canada', 'ontario', 'regional', 'municipal', 'institution')
    ),
    jurisdiction_level TEXT NOT NULL CHECK (
        jurisdiction_level IN (
            'federal',
            'provincial',
            'municipal',
            'regional',
            'institution',
            'nonprofit_other'
        )
    ),
    connector_type TEXT NOT NULL CHECK (
        connector_type IN (
            'api',
            'feed',
            'open_data_portal',
            'file_download',
            'dashboard_only',
            'request_based',
            'partner_only',
            'crowdsourced_registry'
        )
    ),
    access_route TEXT NOT NULL,
    license_reuse_status TEXT NOT NULL CHECK (
        license_reuse_status IN ('approved', 'approved_with_conditions', 'blocked')
    ),
    attribution_requirement TEXT NOT NULL,
    update_cadence TEXT NOT NULL,
    freshness_sensitivity TEXT NOT NULL CHECK (
        freshness_sensitivity IN ('low', 'medium', 'high')
    ),
    operational_risk TEXT NOT NULL CHECK (
        operational_risk IN ('low', 'medium', 'high')
    ),
    recommended_usage_mode TEXT NOT NULL CHECK (
        recommended_usage_mode IN (
            'live_ui',
            'scheduled_ingest',
            'analytics_only',
            'research_only',
            'do_not_use'
        )
    ),
    provenance_url TEXT NOT NULL,
    last_verified_at DATE NOT NULL,
    notes TEXT,
    fallback_source_id TEXT REFERENCES public_data_sources(source_id),
    public_methodology_note TEXT,
    last_refreshed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_public_data_sources_domain
    ON public_data_sources(domain);

CREATE INDEX IF NOT EXISTS idx_public_data_sources_usage_mode
    ON public_data_sources(recommended_usage_mode);

CREATE TABLE IF NOT EXISTS resource_locations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES public_data_sources(source_id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('facility', 'aed')),
    source_record_id TEXT,
    name TEXT NOT NULL,
    province CHAR(2) NOT NULL,
    city TEXT,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    address TEXT,
    postal_code TEXT,
    phone TEXT,
    website_url TEXT,
    reference_status TEXT CHECK (
        reference_status IS NULL OR reference_status IN ('directory_only')
    ),
    location_description TEXT,
    access_notes TEXT,
    crowdsourced BOOLEAN NOT NULL DEFAULT FALSE,
    completeness_status TEXT CHECK (
        completeness_status IS NULL OR completeness_status IN ('incomplete')
    ),
    provenance_url TEXT NOT NULL,
    last_refreshed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resource_locations_kind_province
    ON resource_locations(kind, province);

CREATE INDEX IF NOT EXISTS idx_resource_locations_source_id
    ON resource_locations(source_id);

CREATE TABLE IF NOT EXISTS public_health_alerts (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES public_data_sources(source_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    source_updated_at TIMESTAMPTZ,
    affected_products JSONB NOT NULL DEFAULT '[]'::jsonb,
    provenance_url TEXT NOT NULL,
    last_refreshed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_public_health_alerts_published_at
    ON public_health_alerts(published_at DESC);

CREATE INDEX IF NOT EXISTS idx_public_health_alerts_source_id
    ON public_health_alerts(source_id);

-- Rollback:
-- DROP INDEX IF EXISTS idx_public_health_alerts_source_id;
-- DROP INDEX IF EXISTS idx_public_health_alerts_published_at;
-- DROP TABLE IF EXISTS public_health_alerts;
-- DROP INDEX IF EXISTS idx_resource_locations_source_id;
-- DROP INDEX IF EXISTS idx_resource_locations_kind_province;
-- DROP TABLE IF EXISTS resource_locations;
-- DROP INDEX IF EXISTS idx_public_data_sources_usage_mode;
-- DROP INDEX IF EXISTS idx_public_data_sources_domain;
-- DROP TABLE IF EXISTS public_data_sources;
