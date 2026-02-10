import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";

/**
 * GET /api/data-quality
 *
 * Returns data quality metrics for the system or a specific hospital.
 *
 * Query params:
 *   hospital_id (optional) - quality for a specific hospital
 *   days (optional, default 30) - lookback period
 */

const EXPECTED_SCRAPES_PER_DAY = 96;
const SCRAPE_INTERVAL_MINUTES = 15;

export async function GET(request: Request) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const hospitalId = searchParams.get("hospital_id");
    const days = Math.min(parseInt(searchParams.get("days") ?? "30", 10), 90);

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

  const sources = sourceMetrics.map((row) => {
    const totalHospitals = Number(row.total_hospitals);
    const expected24h = totalHospitals * EXPECTED_SCRAPES_PER_DAY;
    const actual24h = Number(row.measurements_24h);
    const rate24h =
      expected24h > 0 ? Math.min(actual24h / expected24h, 1.0) : 0;

    const expected7d = totalHospitals * EXPECTED_SCRAPES_PER_DAY * 7;
    const actual7d = Number(row.measurements_7d);
    const rate7d = expected7d > 0 ? Math.min(actual7d / expected7d, 1.0) : 0;

    return {
      source_id: row.source_id,
      source_name: row.source_name,
      province: row.province,
      last_24h_success_rate: Math.round(rate24h * 1000) / 1000,
      last_7d_success_rate: Math.round(rate7d * 1000) / 1000,
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
        (acc, s) =>
          acc +
          Math.round(
            s.last_24h_success_rate *
              s.total_hospitals *
              EXPECTED_SCRAPES_PER_DAY,
          ),
        0,
      ),
      total_hospitals_reporting: total24h,
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
      Number(row.scrape_count) / EXPECTED_SCRAPES_PER_DAY,
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
        success_rate: Math.min(currentCount / EXPECTED_SCRAPES_PER_DAY, 1.0),
        actual_scrapes_24h: currentCount,
        expected_scrapes_24h: EXPECTED_SCRAPES_PER_DAY,
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
