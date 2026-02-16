import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";

interface Methodology {
  metric_family: string;
  start_event: string;
  end_event: string;
  statistic_type: string;
}

interface HospitalComparison {
  id: string;
  name: string;
  province: string;
  city: string;
  wait_time: number;
  last_updated: string;
  methodology: Methodology;
}

interface ComparisonResponse {
  hospital_a: HospitalComparison;
  hospital_b: HospitalComparison;
  comparable: boolean;
  divergence_brief: string | null;
  comparison_timestamp: string;
}

function areComparable(a: Methodology, b: Methodology): boolean {
  return (
    a.metric_family === b.metric_family &&
    a.start_event === b.start_event &&
    a.end_event === b.end_event &&
    a.statistic_type === b.statistic_type
  );
}

function generateDivergenceBrief(
  a: Methodology,
  b: Methodology,
): string | null {
  if (areComparable(a, b)) return null;

  const differences: string[] = [];

  if (a.metric_family !== b.metric_family) {
    differences.push(
      `Different metrics: ${a.metric_family} vs ${b.metric_family}`,
    );
  }
  if (a.start_event !== b.start_event) {
    differences.push(
      `Different start points: ${a.start_event} vs ${b.start_event}`,
    );
  }
  if (a.end_event !== b.end_event) {
    differences.push(`Different end points: ${a.end_event} vs ${b.end_event}`);
  }
  if (a.statistic_type !== b.statistic_type) {
    differences.push(
      `Different statistics: ${a.statistic_type} vs ${b.statistic_type}`,
    );
  }

  return (
    "Methodology Divergence: Direct comparison is scientifically invalid. " +
    differences.join("; ") +
    "."
  );
}

async function getHospitalWithMeasurement(hospitalId: string) {
  const sql = getDb();
  const result = await sql`
    SELECT
      h.id,
      h.name,
      h.province,
      h.city,
      h.latitude,
      h.longitude,
      m.value as wait_time,
      m.timestamp_utc as last_updated,
      m.metric_family,
      m.start_event,
      m.end_event,
      m.statistic_type
    FROM hospitals h
    INNER JOIN LATERAL (
      SELECT *
      FROM measurements
      WHERE hospital_id = h.id
      ORDER BY timestamp_utc DESC
      LIMIT 1
    ) m ON true
    WHERE h.id = ${hospitalId}
      AND h.is_visible = true
      AND h.is_verified = true
  `;

  if (result.length === 0) return null;

  const row = result[0];
  return {
    id: row.id,
    name: row.name,
    province: row.province,
    city: row.city,
    wait_time: Number(row.wait_time),
    last_updated: new Date(row.last_updated).toISOString(),
    methodology: {
      metric_family: row.metric_family,
      start_event: row.start_event,
      end_event: row.end_event,
      statistic_type: row.statistic_type,
    },
  };
}

import { CompareQuerySchema } from "@/utils/validations";

import { checkRateLimit } from "@/utils/rate-limit";

export async function GET(request: Request) {
  // 1. Rate Limit
  const rateLimitResponse = await checkRateLimit(request as any);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = CompareQuerySchema.safeParse(rawParams);

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

    const { a: hospitalA, b: hospitalB } = validation.data;

    if (hospitalA === hospitalB) {
      return NextResponse.json(
        {
          success: false,
          error: "Invalid comparison",
          message: "Cannot compare a hospital with itself",
        },
        { status: 400 },
      );
    }

    // Fetch both hospitals with measurements
    const [dataA, dataB] = await Promise.all([
      getHospitalWithMeasurement(hospitalA),
      getHospitalWithMeasurement(hospitalB),
    ]);

    if (!dataA) {
      return NextResponse.json(
        {
          success: false,
          error: "Hospital not found",
          message: `Hospital ${hospitalA} not found or has no measurements`,
        },
        { status: 404 },
      );
    }

    if (!dataB) {
      return NextResponse.json(
        {
          success: false,
          error: "Hospital not found",
          message: `Hospital ${hospitalB} not found or has no measurements`,
        },
        { status: 404 },
      );
    }

    // Check comparability
    const comparable = areComparable(dataA.methodology, dataB.methodology);

    // Generate divergence brief
    const divergenceBrief = comparable
      ? null
      : generateDivergenceBrief(dataA.methodology, dataB.methodology);

    const response: ComparisonResponse = {
      hospital_a: dataA,
      hospital_b: dataB,
      comparable,
      divergence_brief: divergenceBrief,
      comparison_timestamp: new Date().toISOString(),
    };

    return NextResponse.json(
      {
        success: true,
        data: response,
      },
      { headers: publicCacheHeaders(300, 900) },
    );
  } catch (error) {
    console.error("Failed to compare hospitals:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Comparison failed",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}
