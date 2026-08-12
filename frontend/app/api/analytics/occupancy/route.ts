import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS } from "@/utils/cache";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import { resolveHeartbeatStaleThresholdMinutes } from "@/utils/runtime-freshness";

type OccupancyStatus = "available" | "no_reporting_data" | "not_available_yet";

interface OccupancyFieldsAvailability {
  patients_waiting: boolean;
  patients_in_treatment: boolean;
}

import { OccupancyQuerySchema } from "@/utils/validations";

// Current occupancy must reflect source-health changes immediately. A zero TTL
// bypasses the shared in-process response cache.
const OCCUPANCY_CACHE_TTL_MS = 0;

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const rawParams = Object.fromEntries(searchParams.entries());

  const validation = OccupancyQuerySchema.safeParse(rawParams);

  if (!validation.success) {
    return NextResponse.json(
      {
        success: false,
        error: "Validation Error",
        details: validation.error.format(),
      },
      { status: 400, headers: NO_STORE_HEADERS },
    );
  }

  const { province } = validation.data;
  const staleThresholdMinutes = resolveHeartbeatStaleThresholdMinutes();

  try {
    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:analytics:occupancy", {
        province,
        stale_threshold_minutes: staleThresholdMinutes,
      }),
      OCCUPANCY_CACHE_TTL_MS,
      async () => {
        const sql = getDb();

        const occupancyMeasurements = await sql`
          SELECT COUNT(*)::int AS count
          FROM measurements m
          JOIN hospitals h ON h.id = m.hospital_id
          WHERE h.province = ${province}
            AND h.is_visible = true
            AND h.is_verified = true
            AND (
              m.metric_family = 'STRETCHER_OCCUPANCY'
              OR m.patients_waiting IS NOT NULL
              OR m.patients_in_treatment IS NOT NULL
            )
            AND m.timestamp_utc >= NOW() - INTERVAL '24 hours'
        `;

        const hasOccupancyMeasurements =
          Number(occupancyMeasurements[0]?.count ?? 0) > 0;

        const schemaRows = await sql`
          SELECT column_name
          FROM information_schema.columns
          WHERE table_schema = 'public'
            AND table_name = 'measurements'
            AND column_name IN ('patients_waiting', 'patients_in_treatment')
        `;

        const fields: OccupancyFieldsAvailability = {
          patients_waiting: schemaRows.some(
            (row) => row.column_name === "patients_waiting",
          ),
          patients_in_treatment: schemaRows.some(
            (row) => row.column_name === "patients_in_treatment",
          ),
        };

        if (
          !hasOccupancyMeasurements &&
          (!fields.patients_waiting || !fields.patients_in_treatment)
        ) {
          return {
            success: true,
            data: {
              province,
              available: false,
              status: "not_available_yet" as OccupancyStatus,
              generated_at: new Date().toISOString(),
              message:
                "Occupancy metrics are not available from the current provincial feed for this observatory.",
              fields,
              setup_steps: [
                "Verify provincial source publishes occupancy fields",
                "Extend scraper parser to capture occupancy metrics (percentage or raw counts)",
                "Backfill and validate occupancy aggregates before public interpretation",
              ],
            },
          };
        }

        const aggregateRows = await sql`
          WITH relevant_measurements AS (
            SELECT m.*
            FROM measurements m
            JOIN hospitals h ON h.id = m.hospital_id
            WHERE h.province = ${province}
              AND h.is_visible = true
              AND h.is_verified = true
              AND (
                m.metric_family = 'STRETCHER_OCCUPANCY'
                OR m.patients_waiting IS NOT NULL
                OR m.patients_in_treatment IS NOT NULL
              )
              AND m.timestamp_utc >= NOW() - INTERVAL '24 hours'
          ),
          eligible_sources AS (
            SELECT rm.source_id
            FROM relevant_measurements rm
            JOIN scraper_status ss ON ss.source_id = rm.source_id
            WHERE ss.status = 'healthy'
              AND COALESCE(ss.consecutive_failures, 0) = 0
              AND ss.last_run >= NOW() - (
                ${staleThresholdMinutes} * INTERVAL '1 minute'
              )
              AND ss.last_run <= NOW()
            GROUP BY rm.source_id
            HAVING MAX(rm.timestamp_utc) >= NOW() - (
              ${staleThresholdMinutes} * INTERVAL '1 minute'
            )
              AND MAX(rm.timestamp_utc) <= NOW()
          )
          SELECT
            COUNT(*) FILTER (
              WHERE rm.metric_family = 'STRETCHER_OCCUPANCY'
            )::int AS occupancy_observations_24h,
            COUNT(DISTINCT rm.hospital_id) FILTER (
              WHERE rm.metric_family = 'STRETCHER_OCCUPANCY'
            )::int AS occupancy_hospitals_reporting,
            AVG(rm.value) FILTER (
              WHERE rm.metric_family = 'STRETCHER_OCCUPANCY'
            )::float AS avg_occupancy_percentage,
            MIN(rm.value) FILTER (
              WHERE rm.metric_family = 'STRETCHER_OCCUPANCY'
            )::float AS min_occupancy_percentage,
            MAX(rm.value) FILTER (
              WHERE rm.metric_family = 'STRETCHER_OCCUPANCY'
            )::float AS max_occupancy_percentage,
            MAX(rm.timestamp_utc) FILTER (
              WHERE rm.metric_family = 'STRETCHER_OCCUPANCY'
            ) AS latest_occupancy_observation,
            COUNT(*) FILTER (
              WHERE rm.patients_waiting IS NOT NULL
                OR rm.patients_in_treatment IS NOT NULL
            )::int AS raw_count_observations_24h,
            COUNT(DISTINCT rm.hospital_id) FILTER (
              WHERE rm.patients_waiting IS NOT NULL
                OR rm.patients_in_treatment IS NOT NULL
            )::int AS raw_count_hospitals_reporting,
            AVG(rm.patients_waiting) FILTER (
              WHERE rm.patients_waiting IS NOT NULL
                OR rm.patients_in_treatment IS NOT NULL
            )::float AS avg_patients_waiting,
            AVG(rm.patients_in_treatment) FILTER (
              WHERE rm.patients_waiting IS NOT NULL
                OR rm.patients_in_treatment IS NOT NULL
            )::float AS avg_patients_in_treatment,
            MAX(rm.timestamp_utc) FILTER (
              WHERE rm.patients_waiting IS NOT NULL
                OR rm.patients_in_treatment IS NOT NULL
            ) AS latest_raw_count_observation
          FROM relevant_measurements rm
          JOIN eligible_sources es ON es.source_id = rm.source_id
        `;

        const aggregateRow = aggregateRows[0] ?? null;
        const occupancyObservations = Number(
          aggregateRow?.occupancy_observations_24h ?? 0,
        );
        const rawCountObservations = Number(
          aggregateRow?.raw_count_observations_24h ?? 0,
        );
        const totalObservations = occupancyObservations + rawCountObservations;
        const recentObservationCount = Number(
          occupancyMeasurements[0]?.count ?? 0,
        );
        const currentDataAvailable = totalObservations > 0;
        const latestObservationValues = [
          aggregateRow?.latest_occupancy_observation,
          aggregateRow?.latest_raw_count_observation,
        ]
          .filter((value) => value !== null && value !== undefined)
          .map((value) => new Date(value).getTime())
          .filter(Number.isFinite);
        const latestObservation =
          latestObservationValues.length > 0
            ? new Date(Math.max(...latestObservationValues))
            : null;

        const status: OccupancyStatus = currentDataAvailable
          ? "available"
          : "no_reporting_data";

        interface OccupancyResponse {
          province: string;
          available: boolean;
          status: OccupancyStatus;
          generated_at: string;
          message: string;
          fields: OccupancyFieldsAvailability;
          observations_24h: number;
          latest_observation: string | null;
          freshness_threshold_minutes: number;
          occupancy_percentage?: {
            hospitals_reporting: number;
            average: number | null;
            min: number | null;
            max: number | null;
            latest_observation: string | null;
            note: string;
          };
          raw_counts?: {
            hospitals_reporting: number;
            averages: {
              patients_waiting: number | null;
              patients_in_treatment: number | null;
            };
            latest_observation: string | null;
          };
        }

        const responseData: OccupancyResponse = {
          province,
          available: currentDataAvailable,
          status,
          generated_at: new Date().toISOString(),
          message:
            status === "available"
              ? "Occupancy data is available for reporting hospitals."
              : recentObservationCount === 0
                ? "Occupancy fields exist but no reporting rows were found in the last 24 hours."
                : `Current occupancy data are unavailable because source collection or freshness does not meet the ${staleThresholdMinutes}-minute public threshold.`,
          fields,
          observations_24h: totalObservations,
          latest_observation: latestObservation?.toISOString() ?? null,
          freshness_threshold_minutes: staleThresholdMinutes,
        };

        if (currentDataAvailable && occupancyObservations > 0) {
          responseData.occupancy_percentage = {
            hospitals_reporting: Number(
              aggregateRow?.occupancy_hospitals_reporting ?? 0,
            ),
            average:
              aggregateRow?.avg_occupancy_percentage !== null &&
              aggregateRow?.avg_occupancy_percentage !== undefined
                ? Number(aggregateRow.avg_occupancy_percentage)
                : null,
            min:
              aggregateRow?.min_occupancy_percentage !== null &&
              aggregateRow?.min_occupancy_percentage !== undefined
                ? Number(aggregateRow.min_occupancy_percentage)
                : null,
            max:
              aggregateRow?.max_occupancy_percentage !== null &&
              aggregateRow?.max_occupancy_percentage !== undefined
                ? Number(aggregateRow.max_occupancy_percentage)
                : null,
            latest_observation: aggregateRow?.latest_occupancy_observation
              ? String(aggregateRow.latest_occupancy_observation)
              : null,
            note: "Stretcher occupancy rate as percentage. >100% indicates overcrowding.",
          };
        }

        if (currentDataAvailable && rawCountObservations > 0) {
          responseData.raw_counts = {
            hospitals_reporting: Number(
              aggregateRow?.raw_count_hospitals_reporting ?? 0,
            ),
            averages: {
              patients_waiting:
                aggregateRow?.avg_patients_waiting !== null &&
                aggregateRow?.avg_patients_waiting !== undefined
                  ? Number(aggregateRow.avg_patients_waiting)
                  : null,
              patients_in_treatment:
                aggregateRow?.avg_patients_in_treatment !== null &&
                aggregateRow?.avg_patients_in_treatment !== undefined
                  ? Number(aggregateRow.avg_patients_in_treatment)
                  : null,
            },
            latest_observation: aggregateRow?.latest_raw_count_observation
              ? String(aggregateRow.latest_raw_count_observation)
              : null,
          };
        }

        return {
          success: true,
          data: responseData,
        };
      },
    );

    return NextResponse.json(payload, { headers: NO_STORE_HEADERS });
  } catch (error) {
    console.error("Failed to compute occupancy analytics:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute occupancy analytics",
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
