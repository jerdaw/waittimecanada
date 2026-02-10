import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";

export interface SourceHealth {
  source_id: string;
  source_name: string;
  last_run: string | null;
  status: "healthy" | "error" | "stale" | "unknown";
  error_message: string | null;
  measurements_count: number;
  age_minutes: number | null;
}

export interface HealthResponse {
  healthy: boolean;
  last_update: string | null;
  stale_threshold_minutes: number;
  sources: SourceHealth[];
}

const STALE_THRESHOLD_MINUTES = 60;

export async function GET() {
  try {
    const sql = getDb();
    // Get latest heartbeat for each source
    const result = await sql`
      SELECT
        s.id as source_id,
        s.name as source_name,
        ss.last_run,
        ss.status,
        ss.error_message,
        COALESCE(ss.measurements_count, 0) as measurements_count,
        EXTRACT(EPOCH FROM (NOW() - ss.last_run)) / 60 as age_minutes
      FROM sources s
      LEFT JOIN scraper_status ss ON s.id = ss.source_id
      ORDER BY s.province, s.name
    `;

    const sources: SourceHealth[] = result.map((row) => {
      const ageMinutes = row.age_minutes ? Number(row.age_minutes) : null;

      // Determine effective status
      let status: SourceHealth["status"] = "unknown";
      if (!row.last_run) {
        status = "unknown";
      } else if (row.status === "error") {
        status = "error";
      } else if (ageMinutes && ageMinutes > STALE_THRESHOLD_MINUTES) {
        status = "stale";
      } else {
        status = "healthy";
      }

      return {
        source_id: row.source_id,
        source_name: row.source_name,
        last_run: row.last_run ? new Date(row.last_run).toISOString() : null,
        status,
        error_message: row.error_message,
        measurements_count: Number(row.measurements_count),
        age_minutes: ageMinutes ? Math.round(ageMinutes) : null,
      };
    });

    // Overall health: all sources must be healthy
    const healthy = sources.every(
      (s) => s.status === "healthy" || s.status === "unknown",
    );

    // Find the most recent update across all sources
    const lastUpdate = sources
      .filter((s) => s.last_run)
      .sort(
        (a, b) =>
          new Date(b.last_run!).getTime() - new Date(a.last_run!).getTime(),
      )[0]?.last_run;

    return NextResponse.json(
      {
        healthy,
        last_update: lastUpdate || null,
        stale_threshold_minutes: STALE_THRESHOLD_MINUTES,
        sources,
      } as HealthResponse,
      { headers: publicCacheHeaders(120, 300) },
    );
  } catch (error) {
    console.error("Failed to fetch health status:", error);
    return NextResponse.json(
      {
        healthy: false,
        last_update: null,
        stale_threshold_minutes: STALE_THRESHOLD_MINUTES,
        sources: [],
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
