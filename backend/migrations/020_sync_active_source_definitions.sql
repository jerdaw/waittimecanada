-- 020_sync_active_source_definitions.sql
-- Align active source metadata with backend/data/sources/*.json truth
-- Depends on: 004_seed_sources.sql

INSERT INTO sources (
    id, name, province, url, methodology_url,
    telehealth_name, telehealth_number,
    default_metric_family, default_start_event, default_end_event, default_statistic_type
) VALUES
(
    'quebec-msss',
    'Ministère de la Santé et des Services sociaux',
    'QC',
    'https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec',
    NULL,
    'Info-Santé 811',
    '811',
    'TIME_TO_PROVIDER',
    'REGISTRATION',
    'PHYSICIAN',
    'ROLLING_AVG'
),
(
    'ontario-health',
    'Health Quality Ontario',
    'ON',
    'https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments',
    'https://www.hqontario.ca/System-Performance/Emergency-Department-Performance',
    'Health811',
    '811',
    'TIME_TO_PROVIDER',
    'TRIAGE',
    'PHYSICIAN',
    'MEAN'
),
(
    'alberta-ahs',
    'Alberta Health Services',
    'AB',
    'https://www.albertahealthservices.ca/waittimes/Page14230.aspx',
    'https://www.albertahealthservices.ca/waittimes/Page14230.aspx',
    'Health Link 811',
    '811',
    'TIME_TO_PROVIDER',
    'TRIAGE',
    'PHYSICIAN',
    'POINT_ESTIMATE'
),
(
    'bc-phsa',
    'Provincial Health Services Authority',
    'BC',
    'https://edwaittimes.ca',
    'https://www.edwaittimes.ca/about',
    'HealthLink BC',
    '811',
    'TIME_TO_PROVIDER',
    'TRIAGE',
    'PHYSICIAN',
    'P90'
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    province = EXCLUDED.province,
    url = EXCLUDED.url,
    methodology_url = EXCLUDED.methodology_url,
    telehealth_name = EXCLUDED.telehealth_name,
    telehealth_number = EXCLUDED.telehealth_number,
    default_metric_family = EXCLUDED.default_metric_family,
    default_start_event = EXCLUDED.default_start_event,
    default_end_event = EXCLUDED.default_end_event,
    default_statistic_type = EXCLUDED.default_statistic_type,
    updated_at = NOW();

-- Rollback:
-- No destructive rollback. Re-run the previous canonical source seeding step if source definitions must be restored.
