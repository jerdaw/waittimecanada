import { NextRequest, NextResponse } from "next/server";

import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { logger } from "@/utils/logger";
import {
  deriveFreshnessState,
  type AQHIRecord,
  type SourceCatalogRecord,
  type SourceStatusRecord,
} from "@/utils/public-health-hub";
import { checkRateLimit } from "@/utils/rate-limit";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import { ResourceAQHIQuerySchema } from "@/utils/validations";

const AQHI_CACHE_TTL_MS = 900_000;
const AQHI_COLLECTION_URL =
  "https://api.weather.gc.ca/collections/aqhi-forecasts-realtime/items?f=json";
const AQHI_PROVENANCE_URL =
  "https://api.weather.gc.ca/collections/aqhi-forecasts-realtime";
const AQHI_SOURCE_NAME = "AQHI GeoMet";
const AQHI_SOURCE_CATALOG = {
  source_id: "aqhi-geomet",
  domain: "environmental_overlay",
  source_name: AQHI_SOURCE_NAME,
  connector_type: "api",
  access_route: "GeoMet AQHI collection API",
  license_reuse_status: "approved_with_conditions",
  attribution_requirement:
    "Keep Environment and Climate Change Canada provenance visible.",
  update_cadence: "real-time",
  recommended_usage_mode: "live_ui",
  public_methodology_note:
    "Official AQHI forecast from Environment and Climate Change Canada. Conditions may change.",
  provenance_url: AQHI_PROVENANCE_URL,
  last_verified_at: "2026-03-27",
} as const;
const SEARCH_RADII_DEGREES = [0.5, 1.5, 4] as const;

export async function GET(request: NextRequest) {
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());
    const validation = ResourceAQHIQuerySchema.safeParse(rawParams);

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

    const { latitude, longitude } = validation.data;

    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:resources:aqhi", {
        latitude,
        longitude,
      }),
      AQHI_CACHE_TTL_MS,
      async () => {
        const aqhi = await fetchNearestAQHI(latitude, longitude);
        const sourceStatus: SourceStatusRecord = {
          source_id: "aqhi-geomet",
          source_name: AQHI_SOURCE_NAME,
          provenance_url: AQHI_PROVENANCE_URL,
          last_refreshed_at: aqhi?.issued_at ?? null,
          freshness_state: deriveFreshnessState(
            "environmental_overlay",
            aqhi?.issued_at ?? null,
            AQHI_PROVENANCE_URL,
          ),
        };

        return {
          success: true as const,
          data:
            sourceStatus.freshness_state === "suppress"
              ? null
              : (aqhi as AQHIRecord | null),
          meta: {
            latitude,
            longitude,
            source_status: [sourceStatus],
            source_catalog: [
              buildAQHISourceCatalogRecord(sourceStatus),
            ] satisfies SourceCatalogRecord[],
          },
        };
      },
    );

    return NextResponse.json(payload, {
      headers: publicCacheHeaders(900, 1800),
    });
  } catch (error) {
    logger.error("Failed to fetch AQHI", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch AQHI",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}

function buildAQHISourceCatalogRecord(
  sourceStatus: SourceStatusRecord,
): SourceCatalogRecord {
  return {
    ...AQHI_SOURCE_CATALOG,
    last_refreshed_at: sourceStatus.last_refreshed_at,
    freshness_state: sourceStatus.freshness_state,
  };
}

type AQHIFeature = {
  geometry?: {
    coordinates?: [number, number];
  };
  properties?: {
    location_name_en?: string;
    location_id?: string;
    publication_datetime?: string;
    forecast_datetime?: string;
    aqhi?: number;
  };
};

async function fetchNearestAQHI(
  latitude: number,
  longitude: number,
): Promise<AQHIRecord | null> {
  for (const radius of SEARCH_RADII_DEGREES) {
    const bbox = [
      longitude - radius,
      latitude - radius,
      longitude + radius,
      latitude + radius,
    ].join(",");

    const response = await fetch(
      `${AQHI_COLLECTION_URL}&bbox=${bbox}&limit=200`,
      {
        headers: {
          Accept: "application/geo+json",
        },
        next: {
          revalidate: 900,
        },
      },
    );

    if (!response.ok) {
      continue;
    }

    const payload = (await response.json()) as { features?: AQHIFeature[] };
    const features = payload.features ?? [];
    const best = selectBestAQHIFeature(features, latitude, longitude);
    if (best) {
      return best;
    }
  }

  return null;
}

function selectBestAQHIFeature(
  features: AQHIFeature[],
  latitude: number,
  longitude: number,
): AQHIRecord | null {
  const now = Date.now();
  const candidates = features
    .map((feature) => {
      const coordinates = feature.geometry?.coordinates;
      const properties = feature.properties;
      if (
        !coordinates ||
        !properties?.location_id ||
        properties.aqhi === undefined
      ) {
        return null;
      }

      const distanceKm = distanceBetweenKm(
        latitude,
        longitude,
        coordinates[1],
        coordinates[0],
      );
      const issuedAt = properties.publication_datetime ?? null;
      const forecastAt = properties.forecast_datetime ?? null;

      return {
        locationId: properties.location_id,
        locationName: properties.location_name_en ?? properties.location_id,
        distanceKm,
        issuedAt,
        forecastAt,
        aqhiValue: Number(properties.aqhi),
      };
    })
    .filter(
      (candidate): candidate is NonNullable<typeof candidate> =>
        candidate !== null,
    );

  if (candidates.length === 0) {
    return null;
  }

  candidates.sort((left, right) => left.distanceKm - right.distanceKm);
  const nearestLocationId = candidates[0].locationId;
  const nearestCandidates = candidates
    .filter((candidate) => candidate.locationId === nearestLocationId)
    .sort((left, right) => {
      const leftDelta = Math.abs(
        new Date(left.forecastAt ?? left.issuedAt ?? 0).getTime() - now,
      );
      const rightDelta = Math.abs(
        new Date(right.forecastAt ?? right.issuedAt ?? 0).getTime() - now,
      );
      if (leftDelta !== rightDelta) {
        return leftDelta - rightDelta;
      }
      return (
        new Date(right.issuedAt ?? 0).getTime() -
        new Date(left.issuedAt ?? 0).getTime()
      );
    });

  const best = nearestCandidates[0];
  const issuedAt = best.issuedAt ?? new Date().toISOString();

  return {
    location_name: best.locationName,
    aqhi_value: best.aqhiValue,
    category: categorizeAQHI(best.aqhiValue),
    issued_at: issuedAt,
    valid_until: best.forecastAt,
    source_id: "aqhi-geomet",
    source_name: AQHI_SOURCE_NAME,
    provenance_url: AQHI_PROVENANCE_URL,
    last_refreshed_at: issuedAt,
    freshness_state: deriveFreshnessState(
      "environmental_overlay",
      issuedAt,
      AQHI_PROVENANCE_URL,
    ),
    caveat_class: "official_forecast",
  };
}

function categorizeAQHI(value: number): AQHIRecord["category"] {
  if (value <= 3) {
    return "low";
  }
  if (value <= 6) {
    return "moderate";
  }
  if (value <= 10) {
    return "high";
  }
  return "very_high";
}

function distanceBetweenKm(
  latitude: number,
  longitude: number,
  otherLatitude: number,
  otherLongitude: number,
): number {
  const earthRadiusKm = 6371;
  const latitudeDelta = toRadians(otherLatitude - latitude);
  const longitudeDelta = toRadians(otherLongitude - longitude);
  const a =
    Math.sin(latitudeDelta / 2) * Math.sin(latitudeDelta / 2) +
    Math.cos(toRadians(latitude)) *
      Math.cos(toRadians(otherLatitude)) *
      Math.sin(longitudeDelta / 2) *
      Math.sin(longitudeDelta / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return earthRadiusKm * c;
}

function toRadians(value: number) {
  return (value * Math.PI) / 180;
}
