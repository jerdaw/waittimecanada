import { NextResponse, NextRequest } from "next/server";
import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { getPublicApiErrorMessage } from "@/utils/apiErrors";
import { logger } from "@/utils/logger";
import { checkRateLimit } from "@/utils/rate-limit";
import { HospitalQuerySchema } from "@/utils/validations";
import { getPublicHospitals } from "@/utils/public-hospitals";

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

    const payload = await getPublicHospitals({
      province,
      page,
      limit,
      hasPagination,
    });

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
