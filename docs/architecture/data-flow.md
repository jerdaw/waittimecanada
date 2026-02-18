# Data Flow Architecture

This document visualizes the end-to-end journey of data within the WaitTime Canada platform, from provincial sources to the public API.

## 1. Scraper Pipeline (Ingestion)

The ingestion process runs every 15 minutes via GitHub Actions. It prioritizes **Storage Safety** (hashing payloads) and **Ontology Enforcement** (tagging measurements).

```mermaid
graph TD
    Source[Provincial Source<br/>(HTML/JSON)] -->|Fetch| Scraper[Scraper Runtime<br/>(Playwright/BS4)]
    Scraper -->|Parse| Parser[Parser Logic]
    Parser -->|Extract| Raw[Raw Measurement]

    subgraph Validation
        Raw -->|Tag| Ontology[Ontology Enum Tagging]
        Ontology -->|Hash| Sha[SHA256 Payload Hash]
    end

    Sha -->|Write| DB[(PostgreSQL<br/>measurements)]

    subgraph Auditing
        DB -->|Log| Heartbeat[Scraper Status Heartbeat]
    end
```

### Key Principles
*   **No Raw HTML Storage**: We only store the SHA256 hash of the HTML payload to minimize storage liability.
*   **Strict Ontology**: Every measurement is tagged with `Metric_Family`, `Start_Event`, `End_Event`, and `Statistic_Type` at the moment of ingestion.

## 2. Aggregation Pipeline (Transformation)

Raw measurements are ephemeral (30-day retention). The aggregation pipeline transforms them into permanent statistical records.

```mermaid
graph TD
    DB[(PostgreSQL<br/>measurements)] -->|Select| Batch[Raw Data Batch<br/>(30-day window)]

    subgraph Aggregation Service
        Batch -->|Group By| Group[Hospital + Methodology]
        Group -->|Calculate| Stats[Min/Max/Mean/P90]
        Stats -->|Snapshot| Method[Methodology Snapshot]
    end

    Method -->|Upsert| AggDB[(PostgreSQL<br/>measurement_aggregates)]
```

### Key Principles
*   **Methodology Preservation**: If a hospital changes its reporting methodology (e.g., from "Triage" to "Registration"), the aggregate record preserves the methodology *as it was effectively used* during that time period.

## 3. Comparability Logic (Read Path)

When the frontend requests comparison data, the backend enforces scientific validity.

```mermaid
graph LR
    User[User Request<br/>(Compare A vs B)] --> API[API Endpoint]
    API -->|Fetch Latest| DB[(PostgreSQL)]

    subgraph Comparability Engine
        DB -->|Load| MeasA[Measurement A]
        DB -->|Load| MeasB[Measurement B]

        MeasA & MeasB -->|Compare| Check{Ontology Match?}

        Check -->|Yes| Valid[Comparable: True]
        Check -->|No| Invalid[Comparable: False]
        Invalid -->|Generate| Brief[Divergence Brief]
    end

    Valid & Invalid --> Response[JSON Response]
```

### Key Principles
*   **Strict Equality**: Measurements are comparable IF AND ONLY IF `Metric_Family`, `Start_Event`, `End_Event`, and `Statistic_Type` all match.
*   **Divergence Brief**: If not comparable, the system generates a human-readable explanation (e.g., "Hospital A uses P90 while Hospital B uses Average").
