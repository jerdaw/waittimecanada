import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { getPublicApiErrorMessage } from "@/utils/apiErrors";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";

type RegionTrend = "improving" | "stable" | "worsening";

interface RegionSummary {
  region_id: string;
  region_name: string;
  region_code: string;
  hospital_count: number;
  reporting_count: number;
  period_mean: number | null;
  period_median: number | null;
  best_wait: number | null;
  worst_wait: number | null;
  trend: RegionTrend;
  trend_change_percent: number;
  hospital_ids: string[];
  percentile: number | null;
  quartile: 1 | 2 | 3 | 4 | null;
}

interface RegionSummaryRow {
  region_id: string;
  region_name: string;
  region_code: string;
  sort_order: number;
  hospital_count: number;
  reporting_count: number;
  period_mean: number | null;
  period_median: number | null;
  best_wait: number | null;
  worst_wait: number | null;
  previous_period_mean: number | null;
  hospital_ids: string[];
  province_hospital_total: number;
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
  if (!days) return null;
  return { label, days };
}

function computeTrend(
  currentMean: number | null,
  previousMean: number | null,
): RegionTrend {
  if (currentMean === null || previousMean === null || previousMean <= 0) {
    return "stable";
  }

  const changePercent = ((currentMean - previousMean) / previousMean) * 100;
  if (changePercent < -5) return "improving";
  if (changePercent > 5) return "worsening";
  return "stable";
}

function computeTrendChangePercent(
  currentMean: number | null,
  previousMean: number | null,
): number {
  if (currentMean === null || previousMean === null || previousMean <= 0) {
    return 0;
  }
  return Number(
    (((currentMean - previousMean) / previousMean) * 100).toFixed(1),
  );
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

function average(values: number[]): number | null {
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function isMissingRegionsSchemaError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;

  const maybeError = error as { code?: string; message?: string };
  if (maybeError.code !== "42P01") return false;

  const message = maybeError.message ?? "";
  return (
    message.includes(`relation "regions"`) ||
    message.includes(`relation "hospital_regions"`)
  );
}

import { RegionQuerySchema } from "@/utils/validations";

const REGIONS_CACHE_TTL_MS = 300_000;

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = RegionQuerySchema.safeParse(rawParams);

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

    const { province, period } = validation.data;
    const periodConfig = parsePeriod(period);

    if (!periodConfig) {
      return NextResponse.json(
        { success: false, error: "Invalid period config" },
        { status: 500, headers: NO_STORE_HEADERS },
      );
    }

    const normalizedProvince = province.toUpperCase();
    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:analytics:regions", {
        province: normalizedProvince,
        period: periodConfig.label,
      }),
      REGIONS_CACHE_TTL_MS,
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
              ma.hospital_id,
              AVG(ma.mean_value)::float AS period_mean
            FROM measurement_aggregates ma
            WHERE ma.period_type = 'daily'
              AND ma.period_start >= ${currentStart.toISOString()}::timestamptz
              AND ma.period_start < ${now.toISOString()}::timestamptz
            GROUP BY ma.hospital_id
          ),
          previous_period AS (
            SELECT
              ma.hospital_id,
              AVG(ma.mean_value)::float AS period_mean
            FROM measurement_aggregates ma
            WHERE ma.period_type = 'daily'
              AND ma.period_start >= ${previousStart.toISOString()}::timestamptz
              AND ma.period_start < ${currentStart.toISOString()}::timestamptz
            GROUP BY ma.hospital_id
          )
          SELECT
            r.id AS region_id,
            r.name AS region_name,
            r.code AS region_code,
            r.sort_order,
            COUNT(hr.hospital_id)::int AS hospital_count,
            COUNT(cp.hospital_id)::int AS reporting_count,
            AVG(cp.period_mean)::float AS period_mean,
            PERCENTILE_CONT(0.5) WITHIN GROUP
              (ORDER BY cp.period_mean)::float AS period_median,
            MIN(cp.period_mean)::float AS best_wait,
            MAX(cp.period_mean)::float AS worst_wait,
            AVG(pp.period_mean)::float AS previous_period_mean,
            COALESCE(
              ARRAY_AGG(hr.hospital_id ORDER BY hr.hospital_id)
                FILTER (WHERE hr.hospital_id IS NOT NULL),
              ARRAY[]::text[]
            ) AS hospital_ids,
            (
              SELECT COUNT(*)::int
              FROM hospitals h
              WHERE h.province = ${normalizedProvince}
                AND h.is_visible = true
                AND h.is_verified = true
            ) AS province_hospital_total
          FROM regions r
          LEFT JOIN hospital_regions hr ON hr.region_id = r.id
          LEFT JOIN current_period cp ON cp.hospital_id = hr.hospital_id
          LEFT JOIN previous_period pp ON pp.hospital_id = hr.hospital_id
          WHERE r.province = ${normalizedProvince}
          GROUP BY r.id, r.name, r.code, r.sort_order
          ORDER BY r.sort_order, r.name
        `;

        const parsedRows: RegionSummaryRow[] = rows.map((row) => ({
          region_id: String(row.region_id),
          region_name: String(row.region_name),
          region_code: String(row.region_code),
          sort_order: Number(row.sort_order),
          hospital_count: Number(row.hospital_count ?? 0),
          reporting_count: Number(row.reporting_count ?? 0),
          period_mean:
            row.period_mean === null ? null : Number(row.period_mean),
          period_median:
            row.period_median === null ? null : Number(row.period_median),
          best_wait: row.best_wait === null ? null : Number(row.best_wait),
          worst_wait: row.worst_wait === null ? null : Number(row.worst_wait),
          previous_period_mean:
            row.previous_period_mean === null
              ? null
              : Number(row.previous_period_mean),
          hospital_ids: Array.isArray(row.hospital_ids)
            ? row.hospital_ids.map((value) => String(value))
            : [],
          province_hospital_total: Number(row.province_hospital_total ?? 0),
        }));

        const ranked = parsedRows
          .filter((row) => row.period_mean !== null)
          .sort(
            (left, right) =>
              Number(left.period_mean) - Number(right.period_mean),
          );

        const rankIndex = new Map<
          string,
          { percentile: number; quartile: 1 | 2 | 3 | 4 }
        >();
        ranked.forEach((row, index) => {
          const percentile = computePercentile(index + 1, ranked.length);
          rankIndex.set(row.region_id, {
            percentile,
            quartile: computeQuartile(percentile),
          });
        });

        const regions: RegionSummary[] = parsedRows
          .sort((left, right) => left.sort_order - right.sort_order)
          .map((row) => {
            const rank = rankIndex.get(row.region_id) ?? null;
            return {
              region_id: row.region_id,
              region_name: row.region_name,
              region_code: row.region_code,
              hospital_count: row.hospital_count,
              reporting_count: row.reporting_count,
              period_mean: row.period_mean,
              period_median: row.period_median,
              best_wait: row.best_wait,
              worst_wait: row.worst_wait,
              trend: computeTrend(row.period_mean, row.previous_period_mean),
              trend_change_percent: computeTrendChangePercent(
                row.period_mean,
                row.previous_period_mean,
              ),
              hospital_ids: row.hospital_ids,
              percentile: rank?.percentile ?? null,
              quartile: rank?.quartile ?? null,
            };
          });

        const meanValues = regions
          .filter((region) => region.period_mean !== null)
          .map((region) => Number(region.period_mean));

        const mappedHospitalCount = regions.reduce(
          (sum, region) => sum + region.hospital_count,
          0,
        );
        const provinceHospitalTotal =
          parsedRows.length > 0
            ? Number(parsedRows[0].province_hospital_total ?? 0)
            : 0;
        const mappingCoveragePercent =
          provinceHospitalTotal > 0
            ? (mappedHospitalCount / provinceHospitalTotal) * 100
            : 0;

        return {
          success: true,
          data: {
            province: normalizedProvince,
            period: periodConfig.label,
            generated_at: now.toISOString(),
            region_count: regions.length,
            reporting_regions: regions.filter(
              (region) => region.reporting_count > 0,
            ).length,
            hospital_count: mappedHospitalCount,
            mapped_hospital_count: mappedHospitalCount,
            province_hospital_total: provinceHospitalTotal,
            mapping_coverage: {
              mapped_hospitals: mappedHospitalCount,
              total_hospitals: provinceHospitalTotal,
              coverage_percent: Number(mappingCoveragePercent.toFixed(1)),
            },
            province_mean: average(meanValues),
            regions,
          },
        };
      },
    );

    return NextResponse.json(payload, {
      headers: publicCacheHeaders(300, 900),
    });
  } catch (error) {
    if (isMissingRegionsSchemaError(error)) {
      return NextResponse.json(
        {
          success: false,
          setup_required: true,
          error: "Regional analytics schema is not initialized",
          message:
            "Missing regions tables. Run analytics bootstrap to apply migrations and seed Ontario region mappings.",
          setup_steps: [
            "cd backend && uv run python run_migrations.py",
            "cd backend && uv run python -m waittime.cli.seed_regions --file data/regions/ontario-regions.json",
          ],
        },
        { status: 503, headers: NO_STORE_HEADERS },
      );
    }

    console.error("Failed to compute regional analytics:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute regional analytics",
        message: getPublicApiErrorMessage(error),
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
