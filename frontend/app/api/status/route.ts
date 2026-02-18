import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";

/**
 * GET /api/status
 *
 * Returns system-wide operational status including:
 * - Overall health (healthy / degraded / critical)
 * - Per-province scraper uptime (24h / 7d / 30d)
 * - Last heartbeat timestamps
 * - Methodology drift events (last 30 days)
 */

const EXPECTED_SCRAPES_PER_DAY = 96;

export async function GET() {
  try {
    const sql = getDb();

    // Per-source uptime metrics
    const sourceMetrics = await sql`
      SELECT
        s.id            AS source_id,
        s.name          AS source_name,
        s.province,
        (SELECT COUNT(*) FROM measurements m
          WHERE m.source_id = s.id
          AND m.timestamp_utc >= NOW() - INTERVAL '24 hours') AS measurements_24h,
        (SELECT COUNT(*) FROM measurements m
          WHERE m.source_id = s.id
          AND m.timestamp_utc >= NOW() - INTERVAL '7 days')   AS measurements_7d,
        (SELECT COUNT(*) FROM measurements m
          WHERE m.source_id = s.id
          AND m.timestamp_utc >= NOW() - INTERVAL '30 days')  AS measurements_30d,
        (SELECT COUNT(*) FROM hospitals h
          WHERE h.source_id = s.id
          AND h.is_verified = true
          AND h.is_visible = true)                            AS total_hospitals,
        ss.last_run,
        ss.status                                             AS scraper_status,
        EXTRACT(EPOCH FROM (NOW() - ss.last_run)) / 60        AS heartbeat_age_minutes
      FROM sources s
      LEFT JOIN scraper_status ss ON s.id = ss.source_id
      ORDER BY s.province, s.name
    `;

    const sources = sourceMetrics.map((row) => {
      const totalHospitals = Number(row.total_hospitals);

      const expected24h = totalHospitals * EXPECTED_SCRAPES_PER_DAY;
      const expected7d = totalHospitals * EXPECTED_SCRAPES_PER_DAY * 7;
      const expected30d = totalHospitals * EXPECTED_SCRAPES_PER_DAY * 30;

      const rate24h =
        expected24h > 0
          ? Math.min(Number(row.measurements_24h) / expected24h, 1.0)
          : 0;
      const rate7d =
        expected7d > 0
          ? Math.min(Number(row.measurements_7d) / expected7d, 1.0)
          : 0;
      const rate30d =
        expected30d > 0
          ? Math.min(Number(row.measurements_30d) / expected30d, 1.0)
          : 0;

      const heartbeatAge = row.heartbeat_age_minutes
        ? Math.round(Number(row.heartbeat_age_minutes))
        : null;

      return {
        source_id: row.source_id as string,
        source_name: row.source_name as string,
        province: row.province as string,
        uptime_24h: Math.round(rate24h * 1000) / 1000,
        uptime_7d: Math.round(rate7d * 1000) / 1000,
        uptime_30d: Math.round(rate30d * 1000) / 1000,
        total_hospitals: totalHospitals,
        last_heartbeat_age_minutes: heartbeatAge,
        scraper_status: (row.scraper_status as string) ?? "unknown",
        last_run: row.last_run ? (row.last_run as Date).toISOString() : null,
      };
    });

    // Overall status
    const rates = sources.map((s) => s.uptime_24h);
    const avgRate =
      rates.length > 0 ? rates.reduce((a, b) => a + b, 0) / rates.length : 0;
    const overallStatus =
      avgRate >= 0.95 ? "healthy" : avgRate >= 0.8 ? "degraded" : "critical";

    // Recent methodology drift events (last 30 days)
    const driftEvents = await sql`
      SELECT
        source_id,
        previous_period_start,
        current_period_start,
        previous_mean,
        current_mean,
        shift_percent,
        hospitals_analyzed,
        explanation,
        detected_at
      FROM methodology_change_events
      WHERE detected_at >= NOW() - INTERVAL '30 days'
      ORDER BY detected_at DESC
      LIMIT 20
    `;

    return NextResponse.json(
      {
        overall_status: overallStatus,
        system_uptime_24h: Math.round(avgRate * 1000) / 1000,
        sources,
        drift_events: driftEvents.map((e) => ({
          source_id: e.source_id,
          previous_period_start: e.previous_period_start,
          current_period_start: e.current_period_start,
          previous_mean: Number(e.previous_mean),
          current_mean: Number(e.current_mean),
          shift_percent: Number(e.shift_percent),
          hospitals_analyzed: Number(e.hospitals_analyzed),
          explanation: e.explanation,
          detected_at: (e.detected_at as Date).toISOString(),
        })),
        generated_at: new Date().toISOString(),
      },
      { headers: publicCacheHeaders(120, 360) },
    );
  } catch (error) {
    console.error("Failed to fetch system status:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
