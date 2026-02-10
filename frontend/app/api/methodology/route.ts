import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { publicCacheHeaders } from "@/utils/cache";

/**
 * GET /api/methodology
 *
 * Returns detected methodology change events.
 *
 * Query params:
 *   source_id (optional) - filter by source
 *   limit (optional, default 20) - max results
 */

export async function GET(request: Request) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const sourceId = searchParams.get("source_id");
    const limit = Math.min(
      parseInt(searchParams.get("limit") ?? "20", 10),
      100,
    );

    let events;

    if (sourceId) {
      events = await sql`
        SELECT *
        FROM methodology_change_events
        WHERE source_id = ${sourceId}
        ORDER BY detected_at DESC
        LIMIT ${limit}
      `;
    } else {
      events = await sql`
        SELECT *
        FROM methodology_change_events
        ORDER BY detected_at DESC
        LIMIT ${limit}
      `;
    }

    // Transform for frontend
    const results = events.map((event) => ({
      id: event.id,
      source_id: event.source_id,
      detected_at: event.detected_at,
      previous_period: {
        start: event.previous_period_start,
        end: event.previous_period_end,
        mean: Number(event.previous_mean),
      },
      current_period: {
        start: event.current_period_start,
        end: event.current_period_end,
        mean: Number(event.current_mean),
      },
      shift_percent: Number(event.shift_percent),
      hospitals_analyzed: Number(event.hospitals_analyzed),
      explanation: event.explanation,
    }));

    return NextResponse.json(
      { events: results },
      { headers: publicCacheHeaders(60, 300) }, // Cache for 1 min, stale up to 5
    );
  } catch (error) {
    console.error("Failed to fetch methodology changes:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 },
    );
  }
}
