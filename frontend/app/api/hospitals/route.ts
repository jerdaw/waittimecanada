import { NextResponse } from "next/server";
import postgres from "postgres";

// Initialize Postgres client
// Note: DATABASE_URL should be set in .env.local (copied from backend)
const sql = postgres(process.env.DATABASE_URL!, {
  ssl: "require",
});

export interface Hospital {
  id: string;
  name: string;
  province: string;
  city: string;
  latitude: number;
  longitude: number;
  is_verified: boolean;
  is_visible: boolean;
  source_id: string;
  current_wait_time?: number; // in minutes
  last_updated?: string;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const province = searchParams.get("province");

    // Query hospitals with their most recent measurement
    let query = `
      SELECT
        h.id,
        h.name,
        h.province,
        h.city,
        h.latitude,
        h.longitude,
        h.is_verified,
        h.is_visible,
        h.source_id,
        m.value as current_wait_time,
        m.timestamp_utc as last_updated
      FROM hospitals h
      LEFT JOIN LATERAL (
        SELECT value, timestamp_utc
        FROM measurements
        WHERE hospital_id = h.id
        ORDER BY timestamp_utc DESC
        LIMIT 1
      ) m ON true
      WHERE h.is_visible = true AND h.is_verified = true
    `;

    const params: string[] = [];
    if (province) {
      query += ` AND h.province = $1`;
      params.push(province);
    }

    query += ` ORDER BY h.name`;

    const hospitals = await sql.unsafe(query, params);

    return NextResponse.json({
      success: true,
      count: hospitals.length,
      data: hospitals,
    });
  } catch (error) {
    console.error("Failed to fetch hospitals:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch hospitals",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
