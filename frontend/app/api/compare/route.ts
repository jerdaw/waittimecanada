import { NextResponse, NextRequest } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { getPublicApiErrorMessage } from "@/utils/apiErrors";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import {
  type Methodology,
  areMethodologiesComparable,
  generateDivergenceBrief,
} from "@/utils/comparability";
import {
  classifyWaitTime,
  type WaitTimeStatus,
} from "@/utils/wait-time-freshness";

interface HospitalComparison {
  id: string;
  name: string;
  province: string;
  city: string;
  // Present only when the latest measurement is current for its source.
  wait_time: number | null;
  // Monthly average from a monthly source (Ontario Health); never a live value.
  monthly_average_minutes: number | null;
  wait_time_status: WaitTimeStatus;
  // Latest stored measurement: the last report for stale values, or the last
  // check for monthly sources.
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
      m.source_id as measurement_source_id,
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
  const waitTimeStatus = classifyWaitTime({
    sourceId: row.measurement_source_id,
    hasValue: row.wait_time != null,
    latestMeasurement: row.last_updated,
  });
  const value = row.wait_time == null ? null : Number(row.wait_time);
  return {
    id: row.id,
    name: row.name,
    province: row.province,
    city: row.city,
    wait_time: waitTimeStatus === "current" ? value : null,
    monthly_average_minutes: waitTimeStatus === "monthly" ? value : null,
    wait_time_status: waitTimeStatus,
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
        { status: 400, headers: NO_STORE_HEADERS },
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
        { status: 400, headers: NO_STORE_HEADERS },
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

        const hasCurrentValues =
          dataA.wait_time_status === "current" &&
          dataB.wait_time_status === "current";
        const unavailableNames = [dataA, dataB]
          .filter((d) => d.wait_time_status !== "current")
          .map((d) => d.name);

        // Two values are directly comparable only when both are current and the
        // methodologies match.
        const isComparable = comparable && hasCurrentValues;
        const divergenceParts: string[] = [];
        const methodologyBrief = comparable
          ? null
          : generateDivergenceBrief(dataA.methodology, dataB.methodology);
        if (methodologyBrief) divergenceParts.push(methodologyBrief);
        if (!hasCurrentValues) {
          divergenceParts.push(
            `No current value for ${unavailableNames.join(" and ")}: it is either stale or a monthly average, so it cannot be compared with a current wait time.`,
          );
        }
        const divergenceBrief =
          divergenceParts.length > 0 ? divergenceParts.join(" ") : null;

        const response: ComparisonResponse = {
          hospital_a: dataA,
          hospital_b: dataB,
          comparable: isComparable,
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

    return NextResponse.json(payload.body, {
      status: payload.status,
      headers:
        payload.status === 200
          ? publicCacheHeaders(300, 900)
          : NO_STORE_HEADERS,
    });
  } catch (error) {
    console.error("Failed to compare hospitals:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Comparison failed",
        message: getPublicApiErrorMessage(error),
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
