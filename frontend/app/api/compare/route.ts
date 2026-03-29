import { NextResponse, NextRequest } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import {
  type Methodology,
  areMethodologiesComparable,
  generateDivergenceBrief,
} from "@/utils/comparability";

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

async function getHospitalWithMeasurement(
  sql: ReturnType<typeof getDb>,
  hospitalId: string,
) {
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
        AND metric_family = 'TIME_TO_PROVIDER'
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

const COMPARE_CACHE_TTL_MS = 300_000;

export async function GET(request: NextRequest) {
  // 1. Rate Limit
  const rateLimitResponse = await checkRateLimit(request);
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

    const cacheKeyParts =
      hospitalA < hospitalB
        ? { a: hospitalA, b: hospitalB }
        : { a: hospitalB, b: hospitalA };

    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:compare", cacheKeyParts),
      COMPARE_CACHE_TTL_MS,
      async () => {
        const sql = getDb();
        const [dataA, dataB] = await Promise.all([
          getHospitalWithMeasurement(sql, hospitalA),
          getHospitalWithMeasurement(sql, hospitalB),
        ]);

        if (!dataA) {
          return {
            status: 404,
            body: {
              success: false,
              error: "Hospital not found",
              message: `Hospital ${hospitalA} not found or has no measurements`,
            },
          };
        }

        if (!dataB) {
          return {
            status: 404,
            body: {
              success: false,
              error: "Hospital not found",
              message: `Hospital ${hospitalB} not found or has no measurements`,
            },
          };
        }

        const comparable = areMethodologiesComparable(
          dataA.methodology,
          dataB.methodology,
        );

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

        return {
          status: 200,
          body: {
            success: true,
            data: response,
          },
        };
      },
    );

    return NextResponse.json(
      payload.body,
      { status: payload.status, headers: publicCacheHeaders(300, 900) },
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
