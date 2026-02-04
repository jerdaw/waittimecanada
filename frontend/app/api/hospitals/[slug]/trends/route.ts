import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";

// GET /api/hospitals/[slug]/trends?period=24h|7d|30d
//
// Response:
// {
//   hospitalId: string,
//   hospitalName: string,
//   period: "24h" | "7d" | "30d",
//   dataPoints: Array<{
//     timestamp: string,
//     waitTime: number | null,
//   }>,
//   aggregation: "hourly" | "daily"
// }

export async function GET(
  request: Request,
  { params }: { params: { slug: string } }
) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const period = searchParams.get("period") || "24h";

    // Calculate time boundaries
    const now = new Date();
    const start =
      {
        "24h": new Date(now.getTime() - 24 * 60 * 60 * 1000),
        "7d": new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
        "30d": new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
      }[period] || new Date(now.getTime() - 24 * 60 * 60 * 1000);

    // Query with appropriate aggregation
    const aggregation = period === "24h" ? "hour" : "day";

    // Use sql template literal directly with postgres.js
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

    return NextResponse.json({
      hospitalId: params.slug,
      period,
      dataPoints: data.map((d) => ({
        timestamp: d.timestamp,
        waitTime: d.wait_time,
      })),
      aggregation: aggregation === "hour" ? "hourly" : "daily",
    });
  } catch (error) {
    console.error("Failed to fetch trends:", error);
    return NextResponse.json(
      { error: "Failed to fetch trends" },
      { status: 500 }
    );
  }
}
