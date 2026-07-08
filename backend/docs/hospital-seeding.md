# Hospital Data Seeding Guide

This guide explains how to seed hospitals and data sources into the Wait Time Canada database.

## Overview

The seeding process involves three steps:
1. Seed data source definitions (province-level metadata)
2. Seed hospital records
3. Generate test measurements (development only)

## Prerequisites

- PostgreSQL database connection configured in the current environment
- Python virtual environment activated
- Backend package installed in development mode

## Step 1: Seed Data Sources

Data sources represent provincial health authorities that publish wait time data.

### Source Data Format

Create a JSON file in `data/sources/` with the following structure:

```json
{
  "id": "ontario-health",
  "name": "Health Quality Ontario",
  "province": "ON",
  "url": "https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments",
  "methodology_url": "https://www.hqontario.ca/System-Performance/Emergency-Department-Performance",
  "telehealth_number": "811",
  "telehealth_name": "Health811",
  "default_metric_family": "TIME_TO_PROVIDER",
  "default_start_event": "TRIAGE",
  "default_end_event": "PHYSICIAN",
  "default_statistic_type": "MEAN"
}
```

### Seed the Source

```bash
cd backend
python -m waittime.cli.seed_sources --file data/sources/ontario-health.json
```

### List Existing Sources

```bash
python -m waittime.cli.seed_sources --list
```

## Step 2: Seed Hospitals

Hospitals are the facilities that report wait times.

### Hospital Data Format

Create a JSON file in `data/hospitals/` with the following structure:

```json
{
  "source_id": "ontario-health",
  "hospitals": [
    {
      "id": "ca-on-ottawa-civic",
      "name": "The Ottawa Hospital - Civic Campus",
      "province": "ON",
      "city": "Ottawa",
      "latitude": 45.3982,
      "longitude": -75.7370,
      "is_verified": true,
      "is_visible": true
    }
  ]
}
```

### ID Naming Convention

Hospital IDs must follow the format: `ca-{province}-{slug}`

Examples:
- `ca-on-ottawa-civic` - Ottawa Civic Hospital, Ontario
- `ca-qc-chum` - CHUM Hospital, Quebec
- `ca-ab-foothills` - Foothills Hospital, Alberta

### Verification Status

- `is_verified`: Must be manually verified by admin before going live
- `is_visible`: Controls whether hospital appears on public site

**Important:** The verification workflow prevents unvalidated data from appearing on the site. Always set `is_verified=true` for manually curated seed data.

### Seed Hospitals

```bash
cd backend
python -m waittime.cli.seed --file data/hospitals/ontario-seed.json
```

### Dry Run (Validate Only)

```bash
python -m waittime.cli.seed --file data/hospitals/ontario-seed.json --dry-run
```

### List Hospitals by Source

```bash
python -m waittime.cli.seed --source ontario-health --list
```

## Step 3: Generate Test Data (Development)

For development and testing, you can generate synthetic measurements.

### Generate Test Measurements

```bash
cd backend
python -m waittime.cli.generate_test_data --source ontario-health --count 3
```

This creates 3 measurements per hospital with realistic random wait times (60-300 minutes).

### Dry Run

```bash
python -m waittime.cli.generate_test_data --source ontario-health --dry-run
```

## Data Validation

All seed data is validated using Pydantic models:

- **Source validation**: Ensures required fields, valid province codes, valid URLs
- **Hospital validation**: Ensures correct ID format, valid coordinates, required fields
- **Measurement validation**: Ensures valid metric ontology, positive values

If validation fails, the CLI will show detailed error messages.

## Example: Seeding Ontario

```bash
# 1. Seed the Ontario data source
python -m waittime.cli.seed_sources --file data/sources/ontario-health.json

# 2. Seed Ontario hospitals
python -m waittime.cli.seed --file data/hospitals/ontario-seed.json

# 3. Generate test measurements (development)
python -m waittime.cli.generate_test_data --source ontario-health --count 5

# 4. Verify seeding
python -m waittime.cli.seed --source ontario-health --list
```

## Production Considerations

### Real Scraper Data

In production, use actual scrapers instead of test data:

```bash
# Run Ontario scraper
python -m waittime.cli.scraper --source ontario-health

# Run all scrapers
python -m waittime.cli.scraper --all
```

### Hospital Discovery

When scrapers discover new hospitals from trusted government sources, they are auto-approved on insert (`is_verified=true, is_visible=true`). Data quality is enforced through automated monitoring (anomaly detection, payload hashing, heartbeat checks).

### Coordinate Accuracy

Hospital coordinates should be:
- Accurate to at least 4 decimal places
- Verified against official hospital addresses
- Geocoded using the `GeocodingService` if needed

## Troubleshooting

### "Hospital already exists"

If seeding fails because hospitals already exist:

```bash
# Option 1: Skip existing (default behavior)
python -m waittime.cli.seed --file hospitals.json

# Option 2: Update via database service
# Use upsert_hospital() instead of insert_hospital()
```

### "Source not found"

Ensure the data source exists before seeding hospitals:

```bash
python -m waittime.cli.seed_sources --list
```

### Validation Errors

Check that your JSON matches the required schema:

```bash
# Use dry-run to validate without inserting
python -m waittime.cli.seed --file hospitals.json --dry-run
```

## See Also

- [Database Schema](../../docs/architecture/database.md)
- [Ontario Methodology](methodologies/ontario-methodology.md)
- [Integration Testing](integration-testing.md)
