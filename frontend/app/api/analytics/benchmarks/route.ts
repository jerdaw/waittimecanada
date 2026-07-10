import { NextResponse, NextRequest } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { getPublicApiErrorMessage } from "@/utils/apiErrors";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";

type BenchmarkTrend = "improving" | "stable" | "worsening";

interface BenchmarkHospital {
  hospital_id: string;
  hospital_name: string;
  city: string;
  current_wait: number | null;
  period_mean: number;
  percentile: number;
  quartile: 1 | 2 | 3 | 4;
  trend: BenchmarkTrend;
  trend_change_percent: number;
  metric_family: string;
  start_event: string;
  end_event: string;
  statistic_type: string;
}

interface ProvinceStats {
  mean: number | null;
  median: number | null;
  p25: number | null;
  p75: number | null;
  min: number | null;
  max: number | null;
}

const PERIOD_TO_DAYS: Record<string, number> = {
  "24h": 1,
  "7d": 7,
  "30d": 30,
};

function parsePeriod(
  period: string | null,
): { label: string; days: number } | null {
  const label = period ?? "7d";
  const days = PERIOD_TO_DAYS[label];
  if (!days) {
    return null;
  }
  return { label, days };
}

function computeQuantile(sortedValues: number[], q: number): number | null {
  if (sortedValues.length === 0) return null;
  if (sortedValues.length === 1) return sortedValues[0];

  const index = (sortedValues.length - 1) * q;
  const lower = Math.floor(index);
  const upper = Math.min(lower + 1, sortedValues.length - 1);
  const fraction = index - lower;

  if (lower === upper) {
    return sortedValues[lower];
  }
  return (
    sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * fraction
  );
}

function computeProvinceStats(values: number[]): ProvinceStats {
  if (values.length === 0) {
    return {
      mean: null,
      median: null,
      p25: null,
      p75: null,
      min: null,
      max: null,
    };
  }

  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  const median =
    sorted.length % 2 === 0
      ? (sorted[middle - 1] + sorted[middle]) / 2
      : sorted[middle];

  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;

  return {
    mean,
    median,
    p25: computeQuantile(sorted, 0.25),
    p75: computeQuantile(sorted, 0.75),
    min: Math.min(...values),
    max: Math.max(...values),
  };
}

function computePercentile(rank: number, total: number): number {
  if (total <= 0) return 0;
  const percentile = Math.round((rank / total) * 100);
  return Math.min(100, Math.max(1, percentile));
}

function computeQuartile(percentile: number): 1 | 2 | 3 | 4 {
  if (percentile <= 25) return 1;
  if (percentile <= 50) return 2;
  if (percentile <= 75) return 3;
  return 4;
}

function computeTrend(
  currentMean: number,
  previousMean: number | null,
): BenchmarkTrend {
  if (previousMean === null || previousMean <= 0) {
    return "stable";
  }

  const changePercent = ((currentMean - previousMean) / previousMean) * 100;
  if (changePercent < -5) return "improving";
  if (changePercent > 5) return "worsening";
  return "stable";
}

function computeTrendChangePercent(
  currentMean: number,
  previousMean: number | null,
): number {
  if (previousMean === null || previousMean <= 0) {
    return 0;
  }
  return Number(
    (((currentMean - previousMean) / previousMean) * 100).toFixed(1),
  );
}

function computeMethodologyHomogeneity(hospitals: BenchmarkHospital[]) {
  const groupsMap = new Map<string, any>();
  for (const hosp of hospitals) {
    if (!hosp.metric_family) continue;
    const key = `${hosp.metric_family}|${hosp.start_event}|${hosp.end_event}|${hosp.statistic_type}`;
    if (!groupsMap.has(key)) {
      groupsMap.set(key, {
        metric_family: hosp.metric_family,
        start_event: hosp.start_event,
        end_event: hosp.end_event,
        statistic_type: hosp.statistic_type,
        record_count: 0,
      });
    }
    groupsMap.get(key)!.record_count++;
  }

  const groups = Array.from(groupsMap.values());
  const is_homogeneous = groups.length <= 1;

  return {
    is_homogeneous,
    distinct_groups: groups.length,
    divergence_note: is_homogeneous
      ? null
      : `This view contains measurements from ${groups.length} distinct methodology groups. Direct ranking comparison across groups is scientifically invalid.`,
    groups,
  };
}

import { BenchmarkQuerySchema } from "@/utils/validations";

import { checkRateLimit } from "@/utils/rate-limit";

const BENCHMARKS_CACHE_TTL_MS = 300_000;

export async function GET(request: NextRequest) {
  // 1. Rate Limit
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = BenchmarkQuerySchema.safeParse(rawParams);

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

    const { province, period, hospital_id: hospitalId } = validation.data;
    const periodConfig = parsePeriod(period);
    // Zod ensures period is valid, but parsePeriod returns the config object with days

    if (!periodConfig) {
      // Should not happen given Zod schema
      return NextResponse.json(
        { success: false, error: "Invalid period config" },
        { status: 500, headers: NO_STORE_HEADERS },
      );
    }

    const normalizedProvince = province.toUpperCase();
    const cachedBenchmarks = await getOrSetServerCache(
      buildServerCacheKey("api:analytics:benchmarks", {
        province: normalizedProvince,
        period: periodConfig.label,
      }),
      BENCHMARKS_CACHE_TTL_MS,
      async () => {
        const sql = getDb();
        const now = new Date();
        const currentStart = new Date(
          now.getTime() - periodConfig.days * 24 * 60 * 60 * 1000,
        );
        const previousStart = new Date(
          currentStart.getTime() - periodConfig.days * 24 * 60 * 60 * 1000,
        );

        const rows = await sql`
          WITH current_period AS (
            SELECT
              hospital_id,
              AVG(mean_value)::float AS period_mean
            FROM measurement_aggregates
            WHERE period_type = 'daily'
              AND period_start >= ${currentStart.toISOString()}::timestamptz
              AND period_start < ${now.toISOString()}::timestamptz
            GROUP BY hospital_id
          ),
          previous_period AS (
            SELECT
              hospital_id,
              AVG(mean_value)::float AS previous_period_mean
            FROM measurement_aggregates
            WHERE period_type = 'daily'
              AND period_start >= ${previousStart.toISOString()}::timestamptz
              AND period_start < ${currentStart.toISOString()}::timestamptz
            GROUP BY hospital_id
          )
          SELECT
            h.id AS hospital_id,
            h.name AS hospital_name,
            h.city,
            lm.value AS current_wait,
            lm.metric_family,
            lm.start_event,
            lm.end_event,
            lm.statistic_type,
            cp.period_mean,
            pp.previous_period_mean
          FROM hospitals h
          LEFT JOIN LATERAL (
            SELECT value, metric_family, start_event, end_event, statistic_type
            FROM measurements
            WHERE hospital_id = h.id
            ORDER BY timestamp_utc DESC
            LIMIT 1
          ) lm ON true
          LEFT JOIN current_period cp ON cp.hospital_id = h.id
          LEFT JOIN previous_period pp ON pp.hospital_id = h.id
          WHERE h.province = ${normalizedProvince}
            AND h.is_visible = true
            AND h.is_verified = true
          ORDER BY h.id
        `;

        const rankedRows = rows
          .filter((row) => row.period_mean !== null)
          .map((row) => ({
            hospital_id: String(row.hospital_id),
            hospital_name: String(row.hospital_name),
            city: String(row.city),
            current_wait:
              row.current_wait === null ? null : Number(row.current_wait),
            period_mean: Number(row.period_mean),
            previous_period_mean:
              row.previous_period_mean === null
                ? null
                : Number(row.previous_period_mean),
            metric_family: String(row.metric_family ?? "UNKNOWN"),
            start_event: String(row.start_event ?? "UNKNOWN"),
            end_event: String(row.end_event ?? "UNKNOWN"),
            statistic_type: String(row.statistic_type ?? "UNKNOWN"),
          }))
          .sort((left, right) => left.period_mean - right.period_mean);

        const hospitals: BenchmarkHospital[] = rankedRows.map((row, index) => {
          const rank = index + 1;
          const percentile = computePercentile(rank, rankedRows.length);

          return {
            hospital_id: row.hospital_id,
            hospital_name: row.hospital_name,
            city: row.city,
            current_wait: row.current_wait,
            period_mean: row.period_mean,
            percentile,
            quartile: computeQuartile(percentile),
            trend: computeTrend(row.period_mean, row.previous_period_mean),
            trend_change_percent: computeTrendChangePercent(
              row.period_mean,
              row.previous_period_mean,
            ),
            metric_family: row.metric_family,
            start_event: row.start_event,
            end_event: row.end_event,
            statistic_type: row.statistic_type,
          };
        });

        return {
          generated_at: new Date().toISOString(),
          hospital_count: hospitals.length,
          province_stats: computeProvinceStats(
            hospitals.map((hospital) => hospital.period_mean),
          ),
          hospitals,
        };
      },
    );

    const hospitals = cachedBenchmarks.hospitals;

    const selectedHospitals = hospitalId
      ? hospitals.filter((hospital) => hospital.hospital_id === hospitalId)
      : hospitals;

    return NextResponse.json(
      {
        success: true,
        data: {
          province: normalizedProvince,
          period: periodConfig.label,
          generated_at: cachedBenchmarks.generated_at,
          hospital_count: cachedBenchmarks.hospital_count,
          methodology_summary: computeMethodologyHomogeneity(selectedHospitals),
          province_stats: cachedBenchmarks.province_stats,
          hospitals: selectedHospitals,
          ...(hospitalId && selectedHospitals.length === 0
            ? {
                message:
                  "The requested hospital has no benchmarkable aggregate data for this province and period",
              }
            : {}),
        },
      },
      { headers: publicCacheHeaders(300, 900) },
    );
  } catch (error) {
    console.error("Failed to compute benchmarks:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute benchmarks",
        message: getPublicApiErrorMessage(error),
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
