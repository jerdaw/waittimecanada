import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";
import {
  EXPECTED_SCRAPER_RUNS_PER_DAY,
  LIVE_SCRAPER_CADENCE_LABEL,
  getExpectedRunsForDays,
  isActiveLiveScraperSource,
} from "@/utils/live-scraper-sources";

/**
 * GET /api/data-quality
 *
 * Returns data quality metrics for the system or a specific hospital.
 *
 * Query params:
 *   hospital_id (optional) - quality for a specific hospital
 *   days (optional, default 30) - lookback period
 */

import { DataQualityQuerySchema } from "@/utils/validations";

const LEGACY_EXPECTED_SCRAPER_RUNS_PER_DAY = 96;
const LEGACY_SCRAPER_CADENCE_LABEL = "15-minute";
const QUALITY_CADENCE_MODEL_CHANGE_DATE = "2026-03-28";

function buildHistoricalAnnotation(snapshotDates: Date[]) {
  const changeDate = new Date(`${QUALITY_CADENCE_MODEL_CHANGE_DATE}T00:00:00Z`);
  const hasLegacySnapshots = snapshotDates.some((date) => date < changeDate);
  const hasHourlySnapshots = snapshotDates.some((date) => date >= changeDate);

  return {
    has_cadence_model_shift: hasLegacySnapshots && hasHourlySnapshots,
    model_change_date: QUALITY_CADENCE_MODEL_CHANGE_DATE,
    legacy_scheduler_cadence: LEGACY_SCRAPER_CADENCE_LABEL,
    legacy_expected_runs_per_day: LEGACY_EXPECTED_SCRAPER_RUNS_PER_DAY,
    current_scheduler_cadence: LIVE_SCRAPER_CADENCE_LABEL,
    current_expected_runs_per_day: EXPECTED_SCRAPER_RUNS_PER_DAY,
  };
}

export async function GET(request: Request) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = DataQualityQuerySchema.safeParse(rawParams);

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

    const {
      view,
      hospital_id: hospitalId,
      source_id: sourceId,
      days,
      compare_days: compareDays,
    } = validation.data;

    if (view === "trend" && sourceId) {
      return await getSourceTrend(sql, sourceId, days);
    }

    if (view === "diff" && sourceId) {
      return await getSourceDiff(sql, sourceId, compareDays);
    }

    if (hospitalId) {
      return await getHospitalQuality(sql, hospitalId, days);
    }

    return await getSystemQuality(sql);
  } catch (error) {
    console.error("Failed to fetch data quality:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}

async function getSystemQuality(sql: ReturnType<typeof getDb>) {
  // Per-source quality metrics (last 24h and 7d)
  const sourceMetrics = await sql`
    SELECT
      s.id as source_id,
      s.name as source_name,
      s.province,
      (SELECT COUNT(*) FROM measurements m
        WHERE m.source_id = s.id
        AND m.timestamp_utc >= NOW() - INTERVAL '24 hours') as measurements_24h,
      (SELECT COUNT(*) FROM measurements m
        WHERE m.source_id = s.id
        AND m.timestamp_utc >= NOW() - INTERVAL '7 days') as measurements_7d,
      (SELECT COUNT(DISTINCT DATE_TRUNC('hour', m.timestamp_utc)) FROM measurements m
        WHERE m.source_id = s.id
        AND m.timestamp_utc >= NOW() - INTERVAL '24 hours') as runs_24h,
      (SELECT COUNT(DISTINCT DATE_TRUNC('hour', m.timestamp_utc)) FROM measurements m
        WHERE m.source_id = s.id
        AND m.timestamp_utc >= NOW() - INTERVAL '7 days') as runs_7d,
      (SELECT COUNT(DISTINCT m.hospital_id) FROM measurements m
        WHERE m.source_id = s.id
        AND m.timestamp_utc >= NOW() - INTERVAL '24 hours') as hospitals_24h,
      (SELECT COUNT(*) FROM hospitals h
        WHERE h.source_id = s.id
        AND h.is_verified = true
        AND h.is_visible = true) as total_hospitals,
      ss.last_run,
      ss.status as scraper_status,
      EXTRACT(EPOCH FROM (NOW() - ss.last_run)) / 60 as heartbeat_age_minutes
    FROM sources s
    LEFT JOIN scraper_status ss ON s.id = ss.source_id
    ORDER BY s.province, s.name
  `;

  const sources = sourceMetrics
    .filter((row) => isActiveLiveScraperSource(row.source_id as string))
    .map((row) => {
      const totalHospitals = Number(row.total_hospitals);
      const expected24h = EXPECTED_SCRAPER_RUNS_PER_DAY;
      const actual24h = Number(row.runs_24h);
      const rate24h =
        expected24h > 0 ? Math.min(actual24h / expected24h, 1.0) : 0;

      const expected7d = getExpectedRunsForDays(7);
      const actual7d = Number(row.runs_7d);
      const rate7d = expected7d > 0 ? Math.min(actual7d / expected7d, 1.0) : 0;

      return {
        source_id: row.source_id,
        source_name: row.source_name,
        province: row.province,
        last_24h_success_rate: Math.round(rate24h * 1000) / 1000,
        last_7d_success_rate: Math.round(rate7d * 1000) / 1000,
        measurements_24h: Number(row.measurements_24h),
        hospitals_reporting: Number(row.hospitals_24h),
        total_hospitals: totalHospitals,
        last_heartbeat_age_minutes: row.heartbeat_age_minutes
          ? Math.round(Number(row.heartbeat_age_minutes))
          : null,
        scraper_status: row.scraper_status ?? "unknown",
      };
    });

  // Overall status
  const rates = sources.map((s) => s.last_24h_success_rate);
  const avgRate =
    rates.length > 0 ? rates.reduce((a, b) => a + b, 0) / rates.length : 0;
  const overallStatus =
    avgRate >= 0.95 ? "healthy" : avgRate >= 0.8 ? "degraded" : "critical";

  // Total counts
  const total24h = sources.reduce(
    (acc, s) => acc + (Number(s.hospitals_reporting) || 0),
    0,
  );

  return NextResponse.json(
    {
      overall_status: overallStatus,
      sources,
      system_uptime_24h: Math.round(avgRate * 1000) / 1000,
      total_measurements_24h: sources.reduce(
        (acc, s) => acc + s.measurements_24h,
        0,
      ),
      total_hospitals_reporting: total24h,
      scheduler_cadence: LIVE_SCRAPER_CADENCE_LABEL,
      expected_runs_24h: EXPECTED_SCRAPER_RUNS_PER_DAY,
    },
    { headers: publicCacheHeaders(300, 900) },
  );
}

async function getHospitalQuality(
  sql: ReturnType<typeof getDb>,
  hospitalId: string,
  days: number,
) {
  // Coverage timeline
  const timeline = await sql`
    SELECT
      DATE(timestamp_utc) as date,
      COUNT(*) as scrape_count
    FROM measurements
    WHERE hospital_id = ${hospitalId}
      AND timestamp_utc >= NOW() - ${days + " days"}::INTERVAL
    GROUP BY DATE(timestamp_utc)
    ORDER BY date
  `;

  const coverageTimeline = timeline.map((row) => ({
    date: row.date,
    scrape_count: Number(row.scrape_count),
    success_rate: Math.min(
      Number(row.scrape_count) / EXPECTED_SCRAPER_RUNS_PER_DAY,
      1.0,
    ),
  }));

  // Current quality (last 24h)
  const recentCounts = await sql`
    SELECT COUNT(*) as cnt
    FROM measurements
    WHERE hospital_id = ${hospitalId}
      AND timestamp_utc >= NOW() - INTERVAL '24 hours'
  `;
  const currentCount = Number(recentCounts[0]?.cnt ?? 0);

  // Recent anomalies
  const anomalies = await sql`
    SELECT id, value, timestamp_utc, anomaly_reason
    FROM measurements
    WHERE hospital_id = ${hospitalId}
      AND is_anomaly = true
      AND timestamp_utc >= NOW() - INTERVAL '7 days'
    ORDER BY timestamp_utc DESC
    LIMIT 50
  `;

  return NextResponse.json(
    {
      hospital_id: hospitalId,
      coverage_timeline: coverageTimeline,
      current_quality: {
        success_rate: Math.min(
          currentCount / EXPECTED_SCRAPER_RUNS_PER_DAY,
          1.0,
        ),
        actual_scrapes_24h: currentCount,
        expected_scrapes_24h: EXPECTED_SCRAPER_RUNS_PER_DAY,
        scheduler_cadence: LIVE_SCRAPER_CADENCE_LABEL,
      },
      anomalies_7d: anomalies.map((a) => ({
        id: a.id,
        value: Number(a.value),
        timestamp: a.timestamp_utc,
        reason: a.anomaly_reason,
      })),
    },
    { headers: publicCacheHeaders(300, 900) },
  );
}

async function getSourceTrend(
  sql: ReturnType<typeof getDb>,
  sourceId: string,
  days: number,
) {
  const rows = await sql`
    SELECT
      snapshot_date,
      source_id,
      COUNT(hospital_id) AS hospitals_snapshotted,
      AVG(success_rate) AS avg_success_rate,
      MIN(success_rate) AS min_success_rate,
      SUM(CASE WHEN success_rate < 0.8 THEN 1 ELSE 0 END) AS hospitals_critical,
      MAX(longest_gap_minutes) AS worst_gap_minutes
    FROM data_quality_snapshots
    WHERE source_id = ${sourceId}
      AND snapshot_date >= CURRENT_DATE - ${days + " days"}::INTERVAL
    GROUP BY snapshot_date, source_id
    ORDER BY snapshot_date DESC
  `;

  const historicalAnnotation = buildHistoricalAnnotation(
    rows.map((row) => new Date(row.snapshot_date)),
  );

  return NextResponse.json(
    {
      source_id: sourceId,
      days,
      trend: rows.map((r) => ({
        snapshot_date: r.snapshot_date,
        hospitals_snapshotted: Number(r.hospitals_snapshotted),
        avg_success_rate: Number(r.avg_success_rate),
        min_success_rate: Number(r.min_success_rate),
        hospitals_critical: Number(r.hospitals_critical),
        worst_gap_minutes:
          r.worst_gap_minutes !== null ? Number(r.worst_gap_minutes) : null,
      })),
      historical_annotation: historicalAnnotation,
    },
    { headers: publicCacheHeaders(300, 900) },
  );
}

async function getSourceDiff(
  sql: ReturnType<typeof getDb>,
  sourceId: string,
  compareDays: number,
) {
  const trend = await sql`
    SELECT
      snapshot_date,
      AVG(success_rate) AS avg_success_rate,
      COUNT(hospital_id) AS hospitals_snapshotted,
      SUM(CASE WHEN success_rate < 0.8 THEN 1 ELSE 0 END) AS hospitals_critical,
      MAX(longest_gap_minutes) AS worst_gap_minutes
    FROM data_quality_snapshots
    WHERE source_id = ${sourceId}
      AND snapshot_date >= CURRENT_DATE - ${compareDays + 1 + " days"}::INTERVAL
    GROUP BY snapshot_date
    ORDER BY snapshot_date DESC
  `;

  const historicalAnnotation = buildHistoricalAnnotation(
    trend.map((row) => new Date(row.snapshot_date)),
  );

  if (!trend || trend.length === 0) {
    return NextResponse.json(
      {
        has_baseline: false,
        summary: "No historical snapshot data available for comparison.",
        historical_annotation: historicalAnnotation,
      },
      { headers: publicCacheHeaders(300, 900) },
    );
  }

  const current = trend[0];
  const baseline = trend[trend.length - 1];

  if (
    current.snapshot_date.toISOString() === baseline.snapshot_date.toISOString()
  ) {
    return NextResponse.json(
      {
        has_baseline: false,
        summary: "Insufficient historical snapshot data for comparison.",
        historical_annotation: historicalAnnotation,
      },
      { headers: publicCacheHeaders(300, 900) },
    );
  }

  const currRate = Number(current.avg_success_rate) || 0;
  const baseRate = Number(baseline.avg_success_rate) || 0;
  const successRateDelta = currRate - baseRate;

  const currHosp = Number(current.hospitals_snapshotted);
  const baseHosp = Number(baseline.hospitals_snapshotted);
  const hospitalsDelta = currHosp - baseHosp;

  const currGap =
    current.worst_gap_minutes !== null ? Number(current.worst_gap_minutes) : 0;
  const baseGap =
    baseline.worst_gap_minutes !== null
      ? Number(baseline.worst_gap_minutes)
      : 0;
  const worstGapDelta = currGap - baseGap;

  const rateChangePct = successRateDelta * 100;
  let polarity = "Stable";
  if (rateChangePct >= 2.0) {
    polarity = `Improved by ${rateChangePct.toFixed(1)}%`;
  } else if (rateChangePct <= -2.0) {
    polarity = `Degraded by ${Math.abs(rateChangePct).toFixed(1)}%`;
  }

  const summary = `Coverage ${polarity.toLowerCase()} vs. ${compareDays} days ago. Tracking ${currHosp} hospitals (delta: ${hospitalsDelta > 0 ? "+" : ""}${hospitalsDelta}). ${Number(current.hospitals_critical)} hospitals currently reporting critical coverage (<80%).`;

  return NextResponse.json(
    {
      has_baseline: true,
      period_a_date: baseline.snapshot_date,
      period_b_date: current.snapshot_date,
      current_metrics: {
        avg_success_rate: currRate,
        hospitals_snapshotted: currHosp,
        worst_gap_minutes: currGap,
      },
      baseline_metrics: {
        avg_success_rate: baseRate,
        hospitals_snapshotted: baseHosp,
        worst_gap_minutes: baseGap,
      },
      deltas: {
        success_rate_delta: successRateDelta,
        hospitals_reporting_delta: hospitalsDelta,
        worst_gap_delta: worstGapDelta,
      },
      summary,
      historical_annotation: historicalAnnotation,
    },
    { headers: publicCacheHeaders(300, 900) },
  );
}
