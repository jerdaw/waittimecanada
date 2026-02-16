import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";
import { HospitalTrendQuerySchema } from "@/utils/validations";

// GET /api/hospitals/[slug]/trends?period=24h|7d|30d|90d|6m|1y
//
// Response:
// {
//   hospitalId: string,
//   period: string,
//   dataPoints: Array<{
//     timestamp: string,
//     waitTime: number | null,
//     minWaitTime?: number | null,
//     maxWaitTime?: number | null,
//     sampleCount?: number | null,
//   }>,
//   aggregation: "hourly" | "daily" | "weekly" | "monthly",
//   dataSource: "raw" | "aggregated"
// }

// Periods that can be served from raw measurements (within 30-day retention)
const RAW_PERIODS = ["24h", "7d", "30d"];

export async function GET(
  request: Request,
  { params }: { params: { slug: string } },
) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = HospitalTrendQuerySchema.safeParse(rawParams);

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

    const { period } = validation.data;

    // Calculate time boundaries
    const now = new Date();
    const periodMs: Record<string, number> = {
      "24h": 24 * 60 * 60 * 1000,
      "7d": 7 * 24 * 60 * 60 * 1000,
      "30d": 30 * 24 * 60 * 60 * 1000,
      "90d": 90 * 24 * 60 * 60 * 1000,
      "6m": 180 * 24 * 60 * 60 * 1000,
      "1y": 365 * 24 * 60 * 60 * 1000,
    };
    const start = new Date(
      now.getTime() - (periodMs[period] || periodMs["24h"]),
    );

    // For periods within raw retention, use raw measurements
    if (RAW_PERIODS.includes(period)) {
      const aggregation = period === "24h" ? "hour" : "day";

      const data = await sql`
        SELECT
          date_trunc(${aggregation}, timestamp_utc) as timestamp,
          AVG(value)::integer as wait_time
        FROM measurements
        WHERE hospital_id = (SELECT id FROM hospitals WHERE id = ${params.slug} OR name ILIKE ${params.slug})
          AND timestamp_utc >= ${start.toISOString()}
        GROUP BY date_trunc(${aggregation}, timestamp_utc)
        ORDER BY timestamp ASC
      `;

      return NextResponse.json(
        {
          hospitalId: params.slug,
          period,
          dataPoints: data.map((d) => ({
            timestamp: d.timestamp,
            waitTime: d.wait_time,
          })),
          aggregation: aggregation === "hour" ? "hourly" : "daily",
          dataSource: "raw",
        },
        { headers: publicCacheHeaders(600, 1800) },
      );
    }

    // For longer periods, use pre-computed aggregates
    const periodTypeMap: Record<string, string> = {
      "90d": "daily",
      "6m": "weekly",
      "1y": "monthly",
    };
    const periodType = periodTypeMap[period] || "daily";

    const data = await sql`
      SELECT
        period_start as timestamp,
        mean_value::integer as wait_time,
        min_value::integer as min_wait_time,
        max_value::integer as max_wait_time,
        sample_count
      FROM measurement_aggregates
      WHERE hospital_id = (SELECT id FROM hospitals WHERE id = ${params.slug} OR name ILIKE ${params.slug})
        AND period_type = ${periodType}
        AND period_start >= ${start.toISOString()}
      ORDER BY period_start ASC
    `;

    return NextResponse.json(
      {
        hospitalId: params.slug,
        period,
        dataPoints: data.map((d) => ({
          timestamp: d.timestamp,
          waitTime: d.wait_time,
          minWaitTime: d.min_wait_time,
          maxWaitTime: d.max_wait_time,
          sampleCount: d.sample_count,
        })),
        aggregation: periodType,
        dataSource: "aggregated",
      },
      { headers: publicCacheHeaders(600, 1800) },
    );
  } catch (error) {
    console.error("Failed to fetch trends:", error);
    return NextResponse.json(
      { error: "Failed to fetch trends" },
      { status: 500 },
    );
  }
}
