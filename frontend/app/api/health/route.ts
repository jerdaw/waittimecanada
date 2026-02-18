import { NextResponse, NextRequest } from "next/server";
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

interface PostgresInternal {
  options?: { max?: number };
  idle?: number;
  active?: number;
  waiting?: number;
}

export interface DatabaseHealth {
  status: "connected" | "disconnected" | "unknown";
  latency_ms: number | null;
  pool_status?: unknown; // Postgres.js doesn't expose pool stats easily, can be added later if needed
}

export interface HealthResponse {
  healthy: boolean;
  database: DatabaseHealth;
  last_update: string | null;
  stale_threshold_minutes: number;
  sources: SourceHealth[];
}

import { checkRateLimit } from "@/utils/rate-limit";

const STALE_THRESHOLD_MINUTES = 60;

import { logger } from "@/utils/logger";

export async function GET(req: NextRequest) {
  const rateLimitResponse = await checkRateLimit(req);
  if (rateLimitResponse) return rateLimitResponse;

  const healthResponse: Partial<HealthResponse> = {
    healthy: false,
    database: { status: "unknown", latency_ms: null },
    sources: [],
  };

  try {
    const sql = getDb();

    // 1. Check Database Connectivity & Latency
    const start = performance.now();
    try {
      await sql`SELECT 1`;
      const latency = Math.round(performance.now() - start);

      // Access internal pool stats if available (Postgres.js)
      // Note: These are not officially documented public APIs but exist on the instance
      // Note: These are not officially documented public APIs but exist on the instance
      const sqlInternal = sql as unknown as PostgresInternal;

      healthResponse.database = {
        status: "connected",
        latency_ms: latency,
        pool_status: {
            max: sqlInternal.options?.max || 10, // Default is usually 10
            idle: typeof sqlInternal.idle === 'number' ? sqlInternal.idle : null,
            active: typeof sqlInternal.active === 'number' ? sqlInternal.active : null,
            waiting: typeof sqlInternal.waiting === 'number' ? sqlInternal.waiting : null,
        }
      };
    } catch (dbError) {
      logger.error("Database health check failed", dbError); // Use structured logger
      healthResponse.database = {
        status: "disconnected",
        latency_ms: null,
      };
      // If DB is down, we can't really get sources, so return early or continue with empty sources
    }

    // 2. Get latest heartbeat for each source
    // Only proceed if DB is connected
    if (healthResponse.database?.status === "connected") {
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

        healthResponse.sources = sources;
    }

    // Overall health: DB connected AND all sources healthy/unknown
    const dbHealthy = healthResponse.database?.status === "connected";
    const sourcesHealthy = healthResponse.sources!.every(
      (s) => s.status === "healthy" || s.status === "unknown",
    );

    healthResponse.healthy = dbHealthy && sourcesHealthy;

    // Find the most recent update across all sources
    const lastUpdate = healthResponse.sources!
      .filter((s) => s.last_run)
      .sort(
        (a, b) =>
          new Date(b.last_run!).getTime() - new Date(a.last_run!).getTime(),
      )[0]?.last_run;

    return NextResponse.json(
      {
        ...healthResponse,
        last_update: lastUpdate || null,
        stale_threshold_minutes: STALE_THRESHOLD_MINUTES,
      } as HealthResponse,
      { headers: publicCacheHeaders(120, 300) },
    );
  } catch (error) {
    logger.error("Failed to fetch health status", error); // Use structured logger
    return NextResponse.json(
      {
        healthy: false,
        database: { status: "unknown", latency_ms: null },
        last_update: null,
        stale_threshold_minutes: STALE_THRESHOLD_MINUTES,
        sources: [],
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
