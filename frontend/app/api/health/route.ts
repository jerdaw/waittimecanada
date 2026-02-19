import { NextResponse, NextRequest } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { checkRateLimit } from "@/utils/rate-limit";
import { logger } from "@/utils/logger";

export interface SourceHealth {
  source_id: string;
  source_name: string;
  last_run: string | null;
  status: "healthy" | "error" | "stale" | "unknown";
  error_message: string | null;
  measurements_count: number;
  age_minutes: number | null;
  last_success_run: string | null;
  last_success_measurements_count: number | null;
  last_error_run: string | null;
  last_error_category: string | null;
  last_error_stage: string | null;
  consecutive_failures: number;
  last_run_duration_ms: number | null;
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
  pool_status?: unknown;
}

export interface HealthResponse {
  healthy: boolean;
  database: DatabaseHealth;
  last_update: string | null;
  stale_threshold_minutes: number;
  sources: SourceHealth[];
}

const STALE_THRESHOLD_MINUTES = Number(
  process.env.HEARTBEAT_STALE_THRESHOLD_MINUTES ?? "90",
);

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
      const sqlInternal = sql as unknown as PostgresInternal;

      healthResponse.database = {
        status: "connected",
        latency_ms: latency,
        pool_status: {
          max: sqlInternal.options?.max || 10,
          idle: typeof sqlInternal.idle === "number" ? sqlInternal.idle : null,
          active: typeof sqlInternal.active === "number" ? sqlInternal.active : null,
          waiting: typeof sqlInternal.waiting === "number" ? sqlInternal.waiting : null,
        },
      };
    } catch (dbError) {
      logger.error("Database health check failed", dbError);
      healthResponse.database = {
        status: "disconnected",
        latency_ms: null,
      };
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
            ss.last_success_run,
            ss.last_success_measurements_count,
            ss.last_error_run,
            ss.last_error_category,
            ss.last_error_stage,
            ss.consecutive_failures,
            ss.last_run_duration_ms,
            COALESCE(ss.measurements_count, 0) as measurements_count,
            EXTRACT(EPOCH FROM (NOW() - ss.last_run)) / 60 as age_minutes
        FROM sources s
        LEFT JOIN scraper_status ss ON s.id = ss.source_id
        ORDER BY s.province, s.name
        `;

      const sources: SourceHealth[] = result.map((row) => {
        const ageMinutes = row.age_minutes ? Number(row.age_minutes) : null;
        const consecutiveFailures = Number(row.consecutive_failures ?? 0);

        // Determine effective status
        let status: SourceHealth["status"] = "unknown";
        if (!row.last_run) {
          status = "unknown";
        } else if (row.status === "error") {
          status = "error";
        } else if (consecutiveFailures > 0) {
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
          error_message: row.error_message ?? null,
          measurements_count: Number(row.measurements_count),
          age_minutes: ageMinutes ? Math.round(ageMinutes) : null,
          last_success_run: row.last_success_run
            ? new Date(row.last_success_run).toISOString()
            : null,
          last_success_measurements_count:
            row.last_success_measurements_count !== null &&
            row.last_success_measurements_count !== undefined
              ? Number(row.last_success_measurements_count)
              : null,
          last_error_run: row.last_error_run
            ? new Date(row.last_error_run).toISOString()
            : null,
          last_error_category: row.last_error_category ?? null,
          last_error_stage: row.last_error_stage ?? null,
          consecutive_failures: consecutiveFailures,
          last_run_duration_ms:
            row.last_run_duration_ms !== null && row.last_run_duration_ms !== undefined
              ? Number(row.last_run_duration_ms)
              : null,
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
      { headers: NO_STORE_HEADERS },
    );
  } catch (error) {
    logger.error("Failed to fetch health status", error);
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
