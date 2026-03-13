# Data Dictionary

This document serves as the canonical reference for the Wait Time Canada database schema.

## Core Schema

### `sources`
Provincial data source metadata and provenance tracking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | Unique identifier (e.g., `quebec-msss`). |
| `name` | TEXT | Display name of the source. |
| `province` | CHAR(2) | Two-letter province code (ON, QC, etc.). |
| `url` | TEXT | Official data portal URL. |
| `telehealth_name` | TEXT | Local telehealth service name (e.g., "Health Link 811"). |
| `default_metric_family` | ENUM | Default `MetricFamily` for this source. |

### `hospitals`
Healthcare facilities that report wait times.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | Unique identifier (format: `ca-{province}-{slug}`). |
| `name` | TEXT | Official facility name. |
| `source_id` | TEXT (FK) | Link to `sources.id`. |
| `is_verified` | BOOLEAN | **Safety Gate**: Must be TRUE to be visible. |
| `is_visible` | BOOLEAN | Whether to show on the public map. |
| `latitude` | DOUBLE | Geographic coordinate. |

### `measurements`
Individual audit logs of scraped data. **High Volume**.

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Auto-incrementing primary key. |
| `hospital_id` | TEXT (FK) | Link to `hospitals.id`. |
| `timestamp_utc` | TIMESTAMPTZ | When the measurement was recorded. |
| `value` | DOUBLE | Wait time value (usually minutes). |
| `metric_family` | ENUM | Ontology tag: `TIME_TO_PROVIDER`, `TOTAL_LOS`, etc. |
| `start_event` | ENUM | Ontology tag: `TRIAGE`, `REGISTRATION`, etc. |
| `end_event` | ENUM | Ontology tag: `PHYSICIAN`, `DISCHARGE`, etc. |
| `statistic_type` | ENUM | Ontology tag: `P90`, `ROLLING_AVG`, etc. |
| `raw_payload_hash` | CHAR(64) | SHA256 hash of the source HTML (Storage Safety). |

### `scraper_status`
Heartbeat monitor for scraper health.

| Column | Type | Description |
|--------|------|-------------|
| `source_id` | TEXT (PK) | Link to `sources.id`. |
| `last_run` | TIMESTAMPTZ | Time of last scraper attempt (success or failure). |
| `status` | ENUM | `healthy`, `error`, or `stale`. |
| `error_message` | TEXT | Latest error message when status is `error`. |
| `measurements_count` | INTEGER | Measurements persisted in the most recent run. |
| `last_success_run` | TIMESTAMPTZ | Timestamp of the last successful run (last-known-good). |
| `last_success_measurements_count` | INTEGER | Measurement count from the last successful run. |
| `last_error_run` | TIMESTAMPTZ | Timestamp of the most recent failed run. |
| `last_error_category` | TEXT | Structured failure class (`upstream_unavailable`, `parser_breakage`, `infra_runtime`, `persistence_failure`, `unknown`). |
| `last_error_stage` | TEXT | Failure stage (`fetch`, `parse`, `before_save`, `persist`, `heartbeat`, `orchestration`). |
| `consecutive_failures` | INTEGER | Number of consecutive failed runs since last success. |
| `last_run_duration_ms` | INTEGER | Last run duration in milliseconds. |

### `scraper_alert_state`
Persistent alert deduplication state for heartbeat incidents.

| Column | Type | Description |
|--------|------|-------------|
| `source_id` | TEXT (PK/FK) | Link to `sources.id`. |
| `active_incident_kind` | TEXT | Current active incident kind: `stale` or `error`. |
| `active_incident_fingerprint` | TEXT | Stable fingerprint for the active incident. |
| `opened_at` | TIMESTAMPTZ | When the current active incident began. |
| `last_notified_at` | TIMESTAMPTZ | When the active incident last generated a notification attempt. |
| `last_resolved_at` | TIMESTAMPTZ | When the most recent incident for this source was resolved. |
| `updated_at` | TIMESTAMPTZ | Row update timestamp. |

## Analytics & Aggregation

### `measurement_aggregates`
Permanent statistical summaries (hourly/daily/weekly/monthly).

| Column | Type | Description |
|--------|------|-------------|
| `period_type` | TEXT | `hourly`, `daily`, `weekly`, `monthly`. |
| `mean_value` | DOUBLE | Average wait time for this period. |
| `p90_value` | DOUBLE | 90th percentile wait time (if sufficient samples). |
| `metric_family` | TEXT | **Denormalized** ontology snapshot. |

### `regions`
Province region metadata for analytics segmentation.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | Unique identifier. |
| `province` | TEXT | Two-letter province code. |
| `name` | TEXT | Region name (e.g., "Vancouver Coastal"). |

### `hospital_regions`
Many-to-many mapping between hospitals and regions.

| Column | Type | Description |
|--------|------|-------------|
| `region_id` | TEXT (FK) | Link to `regions.id`. |
| `hospital_id` | TEXT (FK) | Link to `hospitals.id`. |
| `is_primary` | BOOLEAN | Whether this is the hospital's primary region. |

### `data_quality_snapshots`
Daily scraper reliability metrics.

| Column | Type | Description |
|--------|------|-------------|
| `snapshot_date` | DATE | The date being analyzed. |
| `success_rate` | DOUBLE | Percentage of expected scrapes that succeeded. |
| `longest_gap_minutes` | INTEGER | Maximum downtime duration in minutes. |

### `methodology_change_events`
Detected shifts in reporting methodology.

| Column | Type | Description |
|--------|------|-------------|
| `detected_at` | TIMESTAMPTZ | When the system flagged the shift. |
| `shift_percent` | DOUBLE | Magnitude of the statistical shift. |
| `explanation` | TEXT | Auto-generated hypothesis for the change. |
