import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";

export interface UnverifiedHospital {
  id: string;
  name: string;
  province: string;
  city: string;
  latitude: number;
  longitude: number;
  source_id: string;
  created_at: string;
  is_visible: boolean;
  is_verified: boolean;
}

/**
 * GET /api/admin/hospitals/unverified
 * Lists all hospitals that have not been verified yet.
 * These are hospitals discovered by scrapers but not yet approved by admin.
 */
export async function GET() {
  try {
    const sql = getDb();
    const hospitals = await sql<UnverifiedHospital[]>`
      SELECT
        id,
        name,
        province,
        city,
        latitude,
        longitude,
        source_id,
        created_at,
        is_visible,
        is_verified
      FROM hospitals
      WHERE is_verified = false
      ORDER BY created_at DESC
    `;

    return NextResponse.json({
      success: true,
      count: hospitals.length,
      data: hospitals,
    });
  } catch (error) {
    console.error("Failed to fetch unverified hospitals:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch unverified hospitals",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
