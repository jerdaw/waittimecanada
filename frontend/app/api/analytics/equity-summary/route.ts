import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import type { EquityFeatureCollection } from "@/utils/equity";
import {
  computeEquityLinkageSummary,
  isDescriptiveEquityAssociation,
  type HospitalWaitPoint,
} from "@/utils/equityInsights";
import { publicCacheHeaders } from "@/utils/cache";
import { loadEquityLayerForProvince } from "@/utils/equityLayerData";
import { RegionQuerySchema } from "@/utils/validations";

type EquitySummaryStatus = "ready" | "no_reporting_data" | "not_available_yet";

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

export async function GET(request: Request) {
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
      { status: 400 },
    );
  }

  const { province, period } = validation.data;
  const periodConfig = parsePeriod(period);

  if (!periodConfig) {
    return NextResponse.json(
      { success: false, error: "Invalid period config" },
      { status: 500 },
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
          is_placeholder: false,
          message:
            "Equity linkage summary is currently enabled for Ontario only while other provincial tract datasets are onboarded.",
          setup_steps: [
            "Integrate provincial census tract income dataset",
            "Enable equity summary calculations for this province",
          ],
        },
      },
      { headers: publicCacheHeaders(300, 900) },
    );
  }

  try {
    let equityData: EquityFeatureCollection;
    try {
      equityData = await loadEquityLayerForProvince(province);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      if (message.includes("not found")) {
        return NextResponse.json(
          {
            success: false,
            error: "Ontario equity layer data not found",
            setup_required: true,
            setup_steps: [
              "Run backend/scripts/prepare_equity_layer.py to generate Ontario layer",
              "Confirm backend/data/layers/ontario-equity-layer.geojson exists",
            ],
          },
          { status: 404 },
        );
      }
      throw error;
    }

    const sql = getDb();
    const now = new Date();
    const periodStart = new Date(
      now.getTime() - periodConfig.days * 24 * 60 * 60 * 1000,
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

    const summary = computeEquityLinkageSummary(hospitalPoints, equityData, 30);
    const isPlaceholder = equityData.features.some(
      (feature) => feature.properties.is_placeholder,
    );

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
          is_placeholder: isPlaceholder,
          message:
            status === "ready"
              ? isPlaceholder
                ? "Equity linkage summary computed from placeholder tract data."
                : "Equity linkage summary computed from Statistics Canada census tract dataset."
              : "No hospital wait aggregates available for linkage in the selected period.",
          methodology: {
            interpretation: isDescriptiveEquityAssociation()
              ? "descriptive_association_only"
              : "unknown",
            causal_inference: false,
            uncertainty_method: "bootstrap_percentile_95ci",
            census_income_reference_year: 2021,
            wait_aggregation_period: periodConfig.label,
            temporal_alignment_note:
              "Income values are from the 2021 Census; wait aggregates use recent windows and are not temporally equivalent.",
          },
          ...summary,
        },
      },
      { headers: publicCacheHeaders(300, 900) },
    );
  } catch (error) {
    console.error("Failed to compute equity linkage summary:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute equity linkage summary",
      },
      { status: 500 },
    );
  }
}
