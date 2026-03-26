import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";

type OccupancyStatus = "available" | "no_reporting_data" | "not_available_yet";

interface OccupancyFieldsAvailability {
  patients_waiting: boolean;
  patients_in_treatment: boolean;
}

import { OccupancyQuerySchema } from "@/utils/validations";

const OCCUPANCY_CACHE_TTL_MS = 300_000;

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
      { status: 400 },
    );
  }

  const { province } = validation.data;

  try {
    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:analytics:occupancy", { province }),
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
            AND m.metric_family = 'STRETCHER_OCCUPANCY'
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

        const occupancyRows = await sql`
          SELECT
            COUNT(*)::int AS observations_24h,
            COUNT(DISTINCT m.hospital_id)::int AS hospitals_reporting,
            AVG(m.value)::float AS avg_occupancy_percentage,
            MIN(m.value)::float AS min_occupancy_percentage,
            MAX(m.value)::float AS max_occupancy_percentage,
            MAX(m.timestamp_utc) AS latest_observation
          FROM measurements m
          JOIN hospitals h ON h.id = m.hospital_id
          WHERE h.province = ${province}
            AND h.is_visible = true
            AND h.is_verified = true
            AND m.metric_family = 'STRETCHER_OCCUPANCY'
            AND m.timestamp_utc >= NOW() - INTERVAL '24 hours'
        `;

        const rawCountRows = await sql`
          SELECT
            COUNT(*)::int AS observations_24h,
            COUNT(DISTINCT m.hospital_id)::int AS hospitals_reporting,
            AVG(m.patients_waiting)::float AS avg_patients_waiting,
            AVG(m.patients_in_treatment)::float AS avg_patients_in_treatment,
            MAX(m.timestamp_utc) AS latest_observation
          FROM measurements m
          JOIN hospitals h ON h.id = m.hospital_id
          WHERE h.province = ${province}
            AND h.is_visible = true
            AND h.is_verified = true
            AND m.timestamp_utc >= NOW() - INTERVAL '24 hours'
            AND (
              m.patients_waiting IS NOT NULL
              OR m.patients_in_treatment IS NOT NULL
            )
        `;

        const occupancyRow = occupancyRows[0] ?? null;
        const rawCountRow = rawCountRows[0] ?? null;

        const occupancyObservations = Number(occupancyRow?.observations_24h ?? 0);
        const rawCountObservations = Number(rawCountRow?.observations_24h ?? 0);
        const totalObservations = occupancyObservations + rawCountObservations;

        const status: OccupancyStatus =
          totalObservations > 0 ? "available" : "no_reporting_data";

        interface OccupancyResponse {
          province: string;
          available: boolean;
          status: OccupancyStatus;
          generated_at: string;
          message: string;
          fields: OccupancyFieldsAvailability;
          observations_24h: number;
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
          available: true,
          status,
          generated_at: new Date().toISOString(),
          message:
            status === "available"
              ? "Occupancy data is available for reporting hospitals."
              : "Occupancy fields exist but no recent reporting rows were found in the last 24 hours.",
          fields,
          observations_24h: totalObservations,
        };

        if (occupancyObservations > 0) {
          responseData.occupancy_percentage = {
            hospitals_reporting: Number(occupancyRow?.hospitals_reporting ?? 0),
            average: occupancyRow?.avg_occupancy_percentage
              ? Number(occupancyRow.avg_occupancy_percentage)
              : null,
            min: occupancyRow?.min_occupancy_percentage
              ? Number(occupancyRow.min_occupancy_percentage)
              : null,
            max: occupancyRow?.max_occupancy_percentage
              ? Number(occupancyRow.max_occupancy_percentage)
              : null,
            latest_observation: occupancyRow?.latest_observation
              ? String(occupancyRow.latest_observation)
              : null,
            note:
              "Stretcher occupancy rate as percentage. >100% indicates overcrowding.",
          };
        }

        if (rawCountObservations > 0) {
          responseData.raw_counts = {
            hospitals_reporting: Number(rawCountRow?.hospitals_reporting ?? 0),
            averages: {
              patients_waiting:
                rawCountRow?.avg_patients_waiting !== null &&
                rawCountRow?.avg_patients_waiting !== undefined
                  ? Number(rawCountRow.avg_patients_waiting)
                  : null,
              patients_in_treatment:
                rawCountRow?.avg_patients_in_treatment !== null &&
                rawCountRow?.avg_patients_in_treatment !== undefined
                  ? Number(rawCountRow.avg_patients_in_treatment)
                  : null,
            },
            latest_observation: rawCountRow?.latest_observation
              ? String(rawCountRow.latest_observation)
              : null,
          };
        }

        return {
          success: true,
          data: responseData,
        };
      },
    );

    return NextResponse.json(
      payload,
      { headers: publicCacheHeaders(300, 900) },
    );
  } catch (error) {
    console.error("Failed to compute occupancy analytics:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute occupancy analytics",
      },
      { status: 500 },
    );
  }
}
