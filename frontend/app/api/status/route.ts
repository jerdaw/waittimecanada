import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";

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
const STATUS_CACHE_TTL_MS = 300_000;

export async function GET() {
  try {
    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:status", {}),
      STATUS_CACHE_TTL_MS,
      async () => {
        const sql = getDb();

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
            last_run: row.last_run
              ? (row.last_run as Date).toISOString()
              : null,
          };
        });

        const rates = sources.map((source) => source.uptime_24h);
        const avgRate =
          rates.length > 0
            ? rates.reduce((sum, value) => sum + value, 0) / rates.length
            : 0;
        const overallStatus =
          avgRate >= 0.95
            ? "healthy"
            : avgRate >= 0.8
              ? "degraded"
              : "critical";

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

        return {
          overall_status: overallStatus,
          system_uptime_24h: Math.round(avgRate * 1000) / 1000,
          sources,
          drift_events: driftEvents.map((event) => ({
            source_id: event.source_id,
            previous_period_start: event.previous_period_start,
            current_period_start: event.current_period_start,
            previous_mean: Number(event.previous_mean),
            current_mean: Number(event.current_mean),
            shift_percent: Number(event.shift_percent),
            hospitals_analyzed: Number(event.hospitals_analyzed),
            explanation: event.explanation,
            detected_at: (event.detected_at as Date).toISOString(),
          })),
          generated_at: new Date().toISOString(),
        };
      },
    );

    return NextResponse.json(
      payload,
      { headers: publicCacheHeaders(300, 900) },
    );
  } catch (error) {
    console.error("Failed to fetch system status:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
