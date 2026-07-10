import { NextResponse, NextRequest } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { getPublicApiErrorMessage } from "@/utils/apiErrors";
import { logger } from "@/utils/logger";
import { checkRateLimit } from "@/utils/rate-limit";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import { HospitalQuerySchema } from "@/utils/validations";

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
  // Methodology fields
  metric_family?: string;
  start_event?: string;
  end_event?: string;
  statistic_type?: string;
  patient_scope?: string;
  // Telehealth fields (from sources)
  telehealth_name?: string;
  telehealth_number?: string;
  // Occupancy fields (Quebec-specific)
  occupancy_percentage?: number; // Stretcher occupancy as percentage
  occupancy_updated?: string; // Timestamp of occupancy measurement
}

const HOSPITALS_CACHE_TTL_MS = 300_000;

export async function GET(request: NextRequest) {
  // 1. Rate Limit
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());

    const validation = HospitalQuerySchema.safeParse(rawParams);

    if (!validation.success) {
      return NextResponse.json(
        {
          success: false,
          error: "Validation Error",
          details: validation.error.format(),
        },
        { status: 400, headers: NO_STORE_HEADERS },
      );
    }

    const { province } = validation.data;
    const page = validation.data.page ?? 1;
    const limit = validation.data.limit ?? 20;
    const hasPagination = searchParams.has("page") || searchParams.has("limit");

    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:hospitals", {
        province: province ?? "all",
        page: hasPagination ? page : undefined,
        limit: hasPagination ? limit : undefined,
      }),
      HOSPITALS_CACHE_TTL_MS,
      async () => {
        const sql = getDb();

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
            s.telehealth_name,
            s.telehealth_number,
            m.value as current_wait_time,
            m.timestamp_utc as last_updated,
            m.metric_family,
            m.start_event,
            m.end_event,
            m.statistic_type,
            m.patient_scope,
            occ.value as occupancy_percentage,
            occ.timestamp_utc as occupancy_updated
          FROM hospitals h
          LEFT JOIN sources s ON s.id = h.source_id
          LEFT JOIN LATERAL (
            SELECT
              value,
              timestamp_utc,
              metric_family,
              start_event,
              end_event,
              statistic_type,
              patient_scope
            FROM measurements
            WHERE hospital_id = h.id
              AND metric_family = 'TIME_TO_PROVIDER'
            ORDER BY timestamp_utc DESC
            LIMIT 1
          ) m ON true
          LEFT JOIN LATERAL (
            SELECT
              value,
              timestamp_utc
            FROM measurements
            WHERE hospital_id = h.id
              AND metric_family = 'STRETCHER_OCCUPANCY'
            ORDER BY timestamp_utc DESC
            LIMIT 1
          ) occ ON true
          WHERE h.is_visible = true AND h.is_verified = true
        `;

        const params: Array<string | number> = [];
        if (province) {
          params.push(province);
          query += ` AND h.province = $${params.length}`;
        }

        query += ` ORDER BY h.name`;

        if (hasPagination) {
          params.push(limit);
          const limitPlaceholder = `$${params.length}`;
          params.push((page - 1) * limit);
          const offsetPlaceholder = `$${params.length}`;
          query += ` LIMIT ${limitPlaceholder} OFFSET ${offsetPlaceholder}`;
        }

        const hospitals = await sql.unsafe(query, params);

        return {
          success: true,
          count: hospitals.length,
          data: hospitals,
        };
      },
    );

    return NextResponse.json(payload, {
      headers: publicCacheHeaders(300, 900),
    });
  } catch (error) {
    logger.error("Failed to fetch hospitals", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch hospitals",
        message: getPublicApiErrorMessage(error),
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
