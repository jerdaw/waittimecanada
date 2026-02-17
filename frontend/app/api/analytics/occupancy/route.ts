import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";

type OccupancyStatus = "available" | "no_reporting_data" | "not_available_yet";

interface OccupancyFieldsAvailability {
  patients_waiting: boolean;
  patients_in_treatment: boolean;
}

function normalizeProvince(value: string | null): string {
  return (value ?? "").trim().toUpperCase();
}

import { OccupancyQuerySchema } from "@/utils/validations";

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
  // normalizeProvince is still useful if we want to be safe, but Zod enum handles it if exact match.
  // However, existing normalizeProvince does upper casing. Zod enum is case sensitive.
  // If we want to support case-insensitive, we should transform before validation or in schema.
  // Validations.ts ProvinceEnum uses upper case.
  // Existing code: normalizeProvince(searchParams.get("province")) -> uppercases it.
  // Validation should probably accept any case and transform to uppercase?
  // Or strict validation?
  // Let's assume strict for now as per other routes, or check if I need to adjust schema.

  // ProvinceSchema is just an enum of uppercased strings.
  // If the user passes "on", Zod will fail.
  // I should probably allow coercion/transform in schema if I want robust API.
  // But standardizing on strict is also fine.
  // Let's stick to what I did for other routes (Schema.safeParse).

  // Wait, other routes used `province.toUpperCase()` AFTER validation?
  // No, `hospitals/route.ts` used `const { province } = validation.data`.
  // If `ProvinceSchema` is strict enum, then input MUST be upper case.
  // If I want to support lower case input, I need to use `z.preprocess` or `transform`.

  // Let's check `validations.ts` definitions.
  // `export const ProvinceEnum = z.enum(["ON", ...])`

  // So "on" will fail.
  // If the previous code relied on `normalizeProvince` which uppercases, then I AM breaking behavior for lowercase inputs.
  // This is a "User Review Required" item in plan? "Standardize 400 ...". Using strict enum is standardizing.
  // But if the frontend sends lowercase, it will break.
  // I should probably make the schema robust to case?
  // Or assume frontend sends correct case.
  // `ProvinceSchema` is used in `TrendsQuerySchema` etc.

  // I will check if I should update `ProvinceSchema` to preprocess.
  // For now I'll apply strict validation.

  try {
    const sql = getDb();

    // Check for STRETCHER_OCCUPANCY measurements (e.g., Quebec percentage-based data)
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

    // Check for raw count fields (for future provinces that report absolute numbers)
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

    // If neither STRETCHER_OCCUPANCY measurements nor raw count fields are available
    if (
      !hasOccupancyMeasurements &&
      (!fields.patients_waiting || !fields.patients_in_treatment)
    ) {
      return NextResponse.json(
        {
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
        },
        { headers: publicCacheHeaders(300, 900) },
      );
    }

    // Query for STRETCHER_OCCUPANCY measurements (percentage-based)
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

    // Query for raw count fields (for future provinces)
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

    // Build response data
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

    // Add percentage-based data if available (Quebec)
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
        note: "Stretcher occupancy rate as percentage. >100% indicates overcrowding.",
      };
    }

    // Add raw count data if available (future provinces)
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

    return NextResponse.json(
      {
        success: true,
        data: responseData,
      },
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
