import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";

/**
 * GET /api/anomalies
 *
 * Returns recent anomalous measurements.
 *
 * Query params:
 *   source_id (optional) - filter by source
 *   days (optional, default 7) - lookback period
 */
import { AnomaliesQuerySchema } from "@/utils/validations";

export async function GET(request: Request) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = AnomaliesQuerySchema.safeParse(rawParams);

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

    const { source_id: sourceId, days } = validation.data;

    let anomalies;

    if (sourceId) {
      anomalies = await sql`
        SELECT
          m.id, m.hospital_id, m.value, m.timestamp_utc,
          m.anomaly_reason, m.source_id,
          h.name as hospital_name, h.province
        FROM measurements m
        JOIN hospitals h ON h.id = m.hospital_id
        WHERE m.is_anomaly = true
          AND m.source_id = ${sourceId}
          AND m.timestamp_utc >= NOW() - ${days + " days"}::INTERVAL
        ORDER BY m.timestamp_utc DESC
        LIMIT 100
      `;
    } else {
      anomalies = await sql`
        SELECT
          m.id, m.hospital_id, m.value, m.timestamp_utc,
          m.anomaly_reason, m.source_id,
          h.name as hospital_name, h.province
        FROM measurements m
        JOIN hospitals h ON h.id = m.hospital_id
        WHERE m.is_anomaly = true
          AND m.timestamp_utc >= NOW() - ${days + " days"}::INTERVAL
        ORDER BY m.timestamp_utc DESC
        LIMIT 100
      `;
    }

    return NextResponse.json(
      {
        anomalies: anomalies.map((a) => ({
          id: a.id,
          hospital_id: a.hospital_id,
          hospital_name: a.hospital_name,
          province: a.province,
          value: Number(a.value),
          timestamp: a.timestamp_utc,
          reason: a.anomaly_reason,
          source_id: a.source_id,
        })),
        total_count: anomalies.length,
      },
      { headers: publicCacheHeaders(300, 900) },
    );
  } catch (error) {
    console.error("Failed to fetch anomalies:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
