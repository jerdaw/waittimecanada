-- 022_update_ontario_health_source_url.sql
-- Align the Ontario active source URL with the current Ontario Health reporting path.
-- Depends on: 020_sync_active_source_definitions.sql

UPDATE sources
SET
    url = 'https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments',
    updated_at = NOW()
WHERE
    id = 'ontario-health'
    AND url <> 'https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments';

-- Rollback:
-- UPDATE sources
-- SET
--     url = 'https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments',
--     updated_at = NOW()
-- WHERE id = 'ontario-health';
