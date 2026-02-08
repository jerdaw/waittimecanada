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

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const province = normalizeProvince(searchParams.get("province"));

  if (!province) {
    return NextResponse.json(
      {
        success: false,
        error: "Missing required parameter",
        message: "Query parameter 'province' is required",
      },
      { status: 400 }
    );
  }

  try {
    const sql = getDb();

    const schemaRows = await sql`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = 'measurements'
        AND column_name IN ('patients_waiting', 'patients_in_treatment')
    `;

    const fields: OccupancyFieldsAvailability = {
      patients_waiting: schemaRows.some((row) => row.column_name === "patients_waiting"),
      patients_in_treatment: schemaRows.some(
        (row) => row.column_name === "patients_in_treatment"
      ),
    };

    if (!fields.patients_waiting || !fields.patients_in_treatment) {
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
              "Extend scraper parser to capture patients_waiting and patients_in_treatment",
              "Backfill and validate occupancy aggregates before public interpretation",
            ],
          },
        },
        { headers: publicCacheHeaders(300, 900) }
      );
    }

    const aggregateRows = await sql`
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

    const row = aggregateRows[0] ?? null;
    const observations = Number(row?.observations_24h ?? 0);
    const hospitalsReporting = Number(row?.hospitals_reporting ?? 0);
    const avgPatientsWaiting =
      row?.avg_patients_waiting === null || row?.avg_patients_waiting === undefined
        ? null
        : Number(row.avg_patients_waiting);
    const avgPatientsInTreatment =
      row?.avg_patients_in_treatment === null || row?.avg_patients_in_treatment === undefined
        ? null
        : Number(row.avg_patients_in_treatment);
    const latestObservation =
      row?.latest_observation === null || row?.latest_observation === undefined
        ? null
        : String(row.latest_observation);

    const status: OccupancyStatus = observations > 0 ? "available" : "no_reporting_data";

    return NextResponse.json(
      {
        success: true,
        data: {
          province,
          available: true,
          status,
          generated_at: new Date().toISOString(),
          message:
            status === "available"
              ? "Occupancy fields are available for reporting hospitals."
              : "Occupancy fields exist in schema but no recent reporting rows were found in the last 24 hours.",
          fields,
          observations_24h: observations,
          hospitals_reporting: hospitalsReporting,
          averages: {
            patients_waiting: avgPatientsWaiting,
            patients_in_treatment: avgPatientsInTreatment,
          },
          latest_observation: latestObservation,
        },
      },
      { headers: publicCacheHeaders(300, 900) }
    );
  } catch (error) {
    console.error("Failed to compute occupancy analytics:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute occupancy analytics",
      },
      { status: 500 }
    );
  }
}
