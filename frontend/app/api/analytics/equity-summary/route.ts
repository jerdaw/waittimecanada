import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { buildPlaceholderEquityFeatureCollection } from "@/utils/equity";
import { computeEquityLinkageSummary, type HospitalWaitPoint } from "@/utils/equityInsights";
import { publicCacheHeaders } from "@/utils/cache";

type EquitySummaryStatus = "ready" | "no_reporting_data" | "not_available_yet";

const PERIOD_TO_DAYS: Record<string, number> = {
  "24h": 1,
  "7d": 7,
  "30d": 30,
};

function parsePeriod(period: string | null): { label: string; days: number } | null {
  const label = period ?? "7d";
  const days = PERIOD_TO_DAYS[label];
  if (!days) return null;
  return { label, days };
}

function normalizeProvince(value: string | null): string {
  return (value ?? "").trim().toUpperCase();
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const province = normalizeProvince(searchParams.get("province"));
  const periodConfig = parsePeriod(searchParams.get("period"));

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

  if (!periodConfig) {
    return NextResponse.json(
      {
        success: false,
        error: "Invalid period",
        message: "Supported period values: 24h, 7d, 30d",
      },
      { status: 400 }
    );
  }

  if (province !== "ON") {
    return NextResponse.json(
      {
        success: true,
        data: {
          province,
          period: periodConfig.label,
          status: "not_available_yet" as EquitySummaryStatus,
          generated_at: new Date().toISOString(),
          is_placeholder: true,
          message:
            "Equity linkage summary is currently scaffolded for Ontario while province-specific tract datasets are onboarded.",
          setup_steps: [
            "Integrate provincial census tract income dataset",
            "Enable equity summary calculations for this province",
          ],
        },
      },
      { headers: publicCacheHeaders(300, 900) }
    );
  }

  try {
    const sql = getDb();
    const now = new Date();
    const periodStart = new Date(
      now.getTime() - periodConfig.days * 24 * 60 * 60 * 1000
    );

    const rows = await sql`
      WITH period_waits AS (
        SELECT
          ma.hospital_id,
          AVG(ma.mean_value)::float AS period_mean
        FROM measurement_aggregates ma
        JOIN hospitals h ON h.id = ma.hospital_id
        WHERE h.province = ${province}
          AND h.is_visible = true
          AND h.is_verified = true
          AND ma.period_type = 'daily'
          AND ma.period_start >= ${periodStart.toISOString()}::timestamptz
          AND ma.period_start < ${now.toISOString()}::timestamptz
        GROUP BY ma.hospital_id
      )
      SELECT
        h.id AS hospital_id,
        h.latitude,
        h.longitude,
        pw.period_mean
      FROM hospitals h
      LEFT JOIN period_waits pw ON pw.hospital_id = h.id
      WHERE h.province = ${province}
        AND h.is_visible = true
        AND h.is_verified = true
      ORDER BY h.id
    `;

    const hospitalPoints: HospitalWaitPoint[] = rows.map((row) => ({
      hospital_id: String(row.hospital_id),
      latitude: Number(row.latitude),
      longitude: Number(row.longitude),
      period_mean:
        row.period_mean === null || row.period_mean === undefined
          ? null
          : Number(row.period_mean),
    }));

    const equityData = buildPlaceholderEquityFeatureCollection(province);
    const summary = computeEquityLinkageSummary(hospitalPoints, equityData, 30);

    const status: EquitySummaryStatus =
      summary.reporting_hospitals > 0 ? "ready" : "no_reporting_data";

    return NextResponse.json(
      {
        success: true,
        data: {
          province,
          period: periodConfig.label,
          status,
          generated_at: new Date().toISOString(),
          is_placeholder: true,
          message:
            status === "ready"
              ? "Equity linkage summary computed using current scaffold tract dataset."
              : "No hospital wait aggregates available for linkage in the selected period.",
          ...summary,
        },
      },
      { headers: publicCacheHeaders(300, 900) }
    );
  } catch (error) {
    console.error("Failed to compute equity linkage summary:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute equity linkage summary",
      },
      { status: 500 }
    );
  }
}
