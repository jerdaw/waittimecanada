-- 004_seed_sources.sql
-- Initial provincial data sources
-- Depends on: 002_create_tables.sql

INSERT INTO sources (
    id, name, province, url, methodology_url,
    telehealth_name, telehealth_number,
    default_metric_family, default_start_event, default_end_event, default_statistic_type
) VALUES
-- Quebec - MSSS
(
    'quebec-msss',
    'Ministère de la Santé et des Services sociaux',
    'QC',
    'https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec',
    NULL,  -- Methodology URL not available on new page
    'Info-Santé 811',
    '811',
    'TIME_TO_PROVIDER',
    'REGISTRATION',
    'PHYSICIAN',
    'ROLLING_AVG'
),
-- Alberta - AHS
(
    'alberta-ahs',
    'Alberta Health Services',
    'AB',
    'https://www.albertahealthservices.ca/waittimes/waittimes.aspx',
    'https://www.albertahealthservices.ca/waittimes/Page14230.aspx',
    'Health Link 811',
    '811',
    'TIME_TO_PROVIDER',
    'TRIAGE',
    'PHYSICIAN',
    'P90'
),
-- Ontario - Health Ontario
(
    'ontario-health',
    'Health Ontario',
    'ON',
    'https://www.ontariohealth.ca/our-work/programs/ontario-wait-times',
    NULL,
    'Health811',
    '811',
    'TIME_TO_PROVIDER',
    'TRIAGE',
    'PHYSICIAN',
    'P90'
),
-- Manitoba - Shared Health
(
    'manitoba-shared-health',
    'Shared Health Manitoba',
    'MB',
    'https://wrha.mb.ca/wait-times/',
    NULL,
    'Health Links – Info Santé',
    '204-788-8200',
    'TIME_TO_PROVIDER',
    'UNKNOWN',
    'FIRST_ASSESSMENT',
    'ALGORITHMIC'
),
-- British Columbia - PHSA
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
-- DELETE FROM sources WHERE id IN (
--     'quebec-msss', 'alberta-ahs', 'ontario-health',
--     'manitoba-shared-health', 'bc-phsa'
-- );
