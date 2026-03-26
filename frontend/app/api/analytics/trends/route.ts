import { NextResponse, NextRequest } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";

type TrendDirection = "improving" | "stable" | "worsening";
type PeriodType = "weekly" | "monthly";

interface TrendPoint {
  period_start: string;
  period_end: string;
  province_mean: number;
  province_median: number;
  province_p90: number;
  hospitals_reporting: number;
  total_measurements: number;
  range_min: number;
  range_max: number;
}

interface AggregateRow {
  hospital_id: string;
  period_start: Date;
  period_end: Date;
  mean_value: number;
  min_value: number;
  max_value: number;
  sample_count: number;
}

const LOOKBACK_TO_MONTHS: Record<string, number> = {
  "3m": 3,
  "6m": 6,
  "1y": 12,
};

function parseLookback(
  lookback: string | null,
): { label: string; months: number } | null {
  const label = lookback ?? "6m";
  const months = LOOKBACK_TO_MONTHS[label];
  if (!months) return null;
  return { label, months };
}

function parsePeriod(period: string | null): PeriodType | null {
  const effective = period ?? "monthly";
  if (effective === "monthly" || effective === "weekly") {
    return effective;
  }
  return null;
}

function computeQuantile(sortedValues: number[], q: number): number {
  if (sortedValues.length === 0) return 0;
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

function weightedMean(values: number[], weights: number[]): number {
  if (!values.length || values.length !== weights.length) return 0;

  const totalWeight = weights.reduce((sum, value) => sum + value, 0);
  if (totalWeight <= 0) return 0;

  const weightedSum = values.reduce(
    (sum, value, index) => sum + value * weights[index],
    0,
  );
  return weightedSum / totalWeight;
}

function startOfWeekUtc(date: Date): Date {
  const midnight = new Date(
    Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()),
  );
  const day = midnight.getUTCDay();
  const daysSinceMonday = (day + 6) % 7;
  return new Date(midnight.getTime() - daysSinceMonday * 24 * 60 * 60 * 1000);
}

function periodBucketStart(date: Date, period: PeriodType): Date {
  if (period === "monthly") {
    return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
  }
  return startOfWeekUtc(date);
}

function periodBucketEnd(start: Date, period: PeriodType): Date {
  if (period === "monthly") {
    return new Date(
      Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 1),
    );
  }
  return new Date(start.getTime() + 7 * 24 * 60 * 60 * 1000);
}

function classifyDirection(
  changePercent: number,
  threshold = 5,
): TrendDirection {
  if (changePercent < -threshold) return "improving";
  if (changePercent > threshold) return "worsening";
  return "stable";
}

function provinceLabel(code: string): string {
  const labels: Record<string, string> = {
    ON: "Ontario",
    QC: "Quebec",
    AB: "Alberta",
    BC: "British Columbia",
    MB: "Manitoba",
    SK: "Saskatchewan",
    NS: "Nova Scotia",
    NB: "New Brunswick",
    NL: "Newfoundland and Labrador",
    PE: "Prince Edward Island",
    NT: "Northwest Territories",
    NU: "Nunavut",
    YT: "Yukon",
  };

  return labels[code] ?? code;
}

function lookbackLabel(label: string): string {
  if (label === "1y") return "1 year";
  return `${label.slice(0, 1)} months`;
}

function narrative(
  province: string,
  direction: TrendDirection,
  changePercent: number,
  startMean: number | null,
  endMean: number | null,
  lookback: string,
): string {
  const provinceName = provinceLabel(province);
  const lookbackText = lookbackLabel(lookback);

  if (startMean === null || endMean === null) {
    return `Not enough data to determine a province-wide emergency wait time trend for ${provinceName} over the past ${lookbackText}.`;
  }

  const roundedStart = Math.round(startMean);
  const roundedEnd = Math.round(endMean);

  if (direction === "improving") {
    return `${provinceName} ER wait times have decreased approximately ${Math.abs(changePercent).toFixed(1)}% over the past ${lookbackText}, from an average of ${roundedStart} minutes to ${roundedEnd} minutes.`;
  }

  if (direction === "worsening") {
    return `${provinceName} ER wait times have increased approximately ${Math.abs(changePercent).toFixed(1)}% over the past ${lookbackText}, from an average of ${roundedStart} minutes to ${roundedEnd} minutes.`;
  }

  return `${provinceName} ER wait times have remained stable over the past ${lookbackText}, holding near ${roundedEnd} minutes on average.`;
}

async function queryAggregateRows(
  sql: ReturnType<typeof getDb>,
  province: string,
  periodType: PeriodType | "daily",
  lookbackStartIso: string,
  metricFamily: string,
): Promise<AggregateRow[]> {
  const rows = await sql`
    SELECT
      ma.hospital_id,
      ma.period_start,
      ma.period_end,
      ma.mean_value,
      ma.min_value,
      ma.max_value,
      ma.sample_count
    FROM measurement_aggregates ma
    JOIN hospitals h ON h.id = ma.hospital_id
    WHERE h.province = ${province}
      AND h.is_visible = true
      AND h.is_verified = true
      AND ma.period_type = ${periodType}
      AND ma.period_start >= ${lookbackStartIso}::timestamptz
      AND ma.metric_family = ${metricFamily}
    ORDER BY ma.period_start ASC, ma.hospital_id ASC
  `;

  return rows.map((row) => ({
    hospital_id: String(row.hospital_id),
    period_start: new Date(String(row.period_start)),
    period_end: new Date(String(row.period_end)),
    mean_value: Number(row.mean_value),
    min_value: Number(row.min_value),
    max_value: Number(row.max_value),
    sample_count: Number(row.sample_count),
  }));
}

function rollupDailyRows(
  dailyRows: AggregateRow[],
  targetPeriod: PeriodType,
): AggregateRow[] {
  const grouped = new Map<
    string,
    {
      hospital_id: string;
      period_start: Date;
      period_end: Date;
      weighted_mean_sum: number;
      sample_count: number;
      min_value: number;
      max_value: number;
    }
  >();

  for (const row of dailyRows) {
    const bucketStart = periodBucketStart(row.period_start, targetPeriod);
    const bucketEnd = periodBucketEnd(bucketStart, targetPeriod);
    const key = `${bucketStart.toISOString()}|${row.hospital_id}`;

    const existing = grouped.get(key);
    if (!existing) {
      grouped.set(key, {
        hospital_id: row.hospital_id,
        period_start: bucketStart,
        period_end: bucketEnd,
        weighted_mean_sum: row.mean_value * row.sample_count,
        sample_count: row.sample_count,
        min_value: row.min_value,
        max_value: row.max_value,
      });
      continue;
    }

    existing.weighted_mean_sum += row.mean_value * row.sample_count;
    existing.sample_count += row.sample_count;
    existing.min_value = Math.min(existing.min_value, row.min_value);
    existing.max_value = Math.max(existing.max_value, row.max_value);
  }

  return Array.from(grouped.values())
    .filter((row) => row.sample_count > 0)
    .map((row) => ({
      hospital_id: row.hospital_id,
      period_start: row.period_start,
      period_end: row.period_end,
      mean_value: row.weighted_mean_sum / row.sample_count,
      min_value: row.min_value,
      max_value: row.max_value,
      sample_count: row.sample_count,
    }))
    .sort((a, b) => {
      const periodDiff = a.period_start.getTime() - b.period_start.getTime();
      if (periodDiff !== 0) return periodDiff;
      return a.hospital_id.localeCompare(b.hospital_id);
    });
}

function buildTrendPoints(rows: AggregateRow[]): TrendPoint[] {
  const grouped = new Map<string, AggregateRow[]>();
  for (const row of rows) {
    const key = row.period_start.toISOString();
    const periodRows = grouped.get(key) ?? [];
    periodRows.push(row);
    grouped.set(key, periodRows);
  }

  return Array.from(grouped.entries())
    .sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())
    .map(([key, periodRows]) => {
      const means = periodRows.map((row) => row.mean_value);
      const sortedMeans = [...means].sort((a, b) => a - b);
      const sampleCounts = periodRows.map((row) => row.sample_count);

      const provinceMean = weightedMean(means, sampleCounts);
      const provinceMedian = computeQuantile(sortedMeans, 0.5);
      const provinceP90 = computeQuantile(sortedMeans, 0.9);

      const periodEnd = periodRows.reduce((latest, row) => {
        return row.period_end > latest ? row.period_end : latest;
      }, periodRows[0].period_end);

      return {
        period_start: new Date(key).toISOString().slice(0, 10),
        period_end: periodEnd.toISOString().slice(0, 10),
        province_mean: Number(provinceMean.toFixed(1)),
        province_median: Number(provinceMedian.toFixed(1)),
        province_p90: Number(provinceP90.toFixed(1)),
        hospitals_reporting: periodRows.length,
        total_measurements: sampleCounts.reduce((sum, value) => sum + value, 0),
        range_min: Number(
          Math.min(...periodRows.map((row) => row.min_value)).toFixed(1),
        ),
        range_max: Number(
          Math.max(...periodRows.map((row) => row.max_value)).toFixed(1),
        ),
      };
    });
}

import { TrendsQuerySchema } from "@/utils/validations";

import { checkRateLimit } from "@/utils/rate-limit";

const TRENDS_CACHE_TTL_MS = 300_000;

async function queryMethodologyContext(
  sql: ReturnType<typeof getDb>,
  province: string,
  lookbackStartIso: string,
  metricFamily: string,
) {
  const groups = await sql`
    SELECT
      ma.metric_family,
      ma.start_event,
      ma.end_event,
      ma.statistic_type,
      COUNT(DISTINCT ma.hospital_id) as hospital_count
    FROM measurement_aggregates ma
    JOIN hospitals h ON h.id = ma.hospital_id
    WHERE h.province = ${province}
      AND h.is_visible = true
      AND h.is_verified = true
      AND ma.period_start >= ${lookbackStartIso}::timestamptz
      AND ma.metric_family = ${metricFamily}
    GROUP BY ma.metric_family, ma.start_event, ma.end_event, ma.statistic_type
    ORDER BY hospital_count DESC
  `;

  const distinct_groups = groups.length;
  const is_homogeneous = distinct_groups <= 1;
  const divergence_note = is_homogeneous
    ? null
    : `This trend mixes measurements from ${distinct_groups} distinct methodology groups. Direct comparison of hospitals across these groups is scientifically invalid.`;

  return {
    distinct_groups,
    is_homogeneous,
    divergence_note,
    groups: groups.map((g) => ({
      metric_family: String(g.metric_family),
      start_event: String(g.start_event),
      end_event: String(g.end_event),
      statistic_type: String(g.statistic_type),
      hospital_count: Number(g.hospital_count),
    })),
  };
}

export async function GET(request: NextRequest) {
  // 1. Rate Limit
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = TrendsQuerySchema.safeParse(rawParams);

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

    const { province, period, lookback, metric_family } = validation.data;

    // Convert Zod's lookback string (e.g. "6m") to the object expected by logic
    const lookbackConfig = parseLookback(lookback);
    // Note: Zod already validated it's a valid enum, so parseLookback should generally succeed,
    // but we can keep the check if we want safety or update logic to trust Zod.
    // However, parseLookback returns { label, months } which we need.

    if (!lookbackConfig) {
      // Should not happen if Zod schema is correct
      return NextResponse.json(
        { success: false, error: "Invalid lookback configuration" },
        { status: 500 },
      );
    }

    const normalizedProvince = province.toUpperCase();
    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:analytics:trends", {
        province: normalizedProvince,
        period,
        lookback: lookbackConfig.label,
        metric_family,
      }),
      TRENDS_CACHE_TTL_MS,
      async () => {
        const sql = getDb();
        const now = new Date();
        const lookbackStart = new Date(
          now.getTime() - lookbackConfig.months * 31 * 24 * 60 * 60 * 1000,
        );

        const lookbackStartIso = lookbackStart.toISOString();

        const [methodologyContext, aggregateRowsResult] = await Promise.all([
          queryMethodologyContext(
            sql,
            normalizedProvince,
            lookbackStartIso,
            metric_family,
          ),
          queryAggregateRows(
            sql,
            normalizedProvince,
            period,
            lookbackStartIso,
            metric_family,
          ),
        ]);

        let aggregateRows = aggregateRowsResult;
        let fallbackSource: "none" | "daily_rollup" = "none";

        if (aggregateRows.length === 0) {
          const dailyRows = await queryAggregateRows(
            sql,
            normalizedProvince,
            "daily",
            lookbackStartIso,
            metric_family,
          );
          if (dailyRows.length > 0) {
            aggregateRows = rollupDailyRows(dailyRows, period);
            fallbackSource = "daily_rollup";
          }
        }

        const dataPoints = buildTrendPoints(aggregateRows);

        const startMean =
          dataPoints.length > 0 ? dataPoints[0].province_mean : null;
        const endMean =
          dataPoints.length > 0
            ? dataPoints[dataPoints.length - 1].province_mean
            : null;

        let changePercent = 0;
        if (startMean !== null && endMean !== null && startMean > 0) {
          changePercent = Number(
            (((endMean - startMean) / startMean) * 100).toFixed(1),
          );
        }

        const direction = classifyDirection(changePercent);

        return {
          success: true,
          data: {
            province: normalizedProvince,
            period,
            lookback: lookbackConfig.label,
            generated_at: now.toISOString(),
            data_source:
              fallbackSource === "none" ? "precomputed" : "derived_from_daily",
            fallback_used: fallbackSource !== "none",
            methodology_context: methodologyContext,
            data_points: dataPoints,
            trend_summary: {
              direction,
              change_percent: changePercent,
              start_mean: startMean,
              end_mean: endMean,
              narrative: narrative(
                normalizedProvince,
                direction,
                changePercent,
                startMean,
                endMean,
                lookbackConfig.label,
              ),
            },
          },
        };
      },
    );

    return NextResponse.json(
      payload,
      { headers: publicCacheHeaders(300, 900) },
    );
  } catch (error) {
    console.error("Failed to compute system trends:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute system trends",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}
