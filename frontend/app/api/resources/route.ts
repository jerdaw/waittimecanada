import { NextRequest, NextResponse } from "next/server";

import { publicCacheHeaders } from "@/utils/cache";
import { getDb } from "@/utils/db";
import { logger } from "@/utils/logger";
import {
  buildSourceStatusRecords,
  calculateDistanceKm,
  deriveFreshnessState,
  type ResourceRecord,
  type ResourceKind,
} from "@/utils/public-health-hub";
import { checkRateLimit } from "@/utils/rate-limit";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import { ResourcesQuerySchema } from "@/utils/validations";

type ResourceRow = {
  id: string;
  kind: ResourceKind;
  name: string;
  province: string;
  city: string | null;
  latitude: number;
  longitude: number;
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | Date | null;
  address: string | null;
  postal_code: string | null;
  phone: string | null;
  website_url: string | null;
  reference_status: "directory_only" | null;
  location_description: string | null;
  access_notes: string | null;
  crowdsourced: boolean;
  completeness_status: "incomplete" | null;
};

const RESOURCES_CACHE_TTL_MS = 300_000;
const EMERGENCY_FACILITY_KEYWORDS = [
  "emergency",
  "urgent care",
  "urgent treatment",
  "hospital",
] as const;
const COMMUNITY_FACILITY_KEYWORDS = [
  "community health",
  "health centre",
  "health center",
  "medical clinic",
  "walk-in",
  "walk in",
  "family health",
  "nurse practitioner",
  "primary care",
  "sexual health",
  "mental health",
  "public health",
] as const;
const PHARMACY_KEYWORDS = ["pharmacy", "drug store"] as const;
const DIAGNOSTIC_FACILITY_KEYWORDS = [
  "ultrasound",
  "radiography",
  "mammography",
  "diagnostic",
  "imaging",
  "x-ray",
  "xray",
  "laboratory",
  "lab",
  "dxa",
  "fluoroscopy",
  "nuclear medicine",
] as const;
const QUERY_TOKEN_SEPARATOR = /[^a-z0-9]+/g;

export async function GET(request: NextRequest) {
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());
    const validation = ResourcesQuerySchema.safeParse(rawParams);

    if (!validation.success) {
      return NextResponse.json(
        {
          success: false,
          error: "Validation Error",
          details: validation.error.format(),
        },
        { status: 400 },
      );
    }

    const { kind, q, province, latitude, longitude, radius, limit } =
      validation.data;

    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:resources", {
        kind,
        q: q ?? null,
        province: province ?? null,
        latitude: latitude ?? null,
        longitude: longitude ?? null,
        radius,
        limit,
      }),
      RESOURCES_CACHE_TTL_MS,
      async () => {
        const sql = getDb();
        const domain = kind === "facility" ? "provider_facility" : "aed";

        const queryParts = [
          `
          SELECT
            rl.id,
            rl.kind,
            rl.name,
            rl.province,
            rl.city,
            rl.latitude,
            rl.longitude,
            rl.source_id,
            pds.source_name,
            COALESCE(rl.provenance_url, pds.provenance_url) AS provenance_url,
            COALESCE(rl.last_refreshed_at, pds.last_refreshed_at) AS last_refreshed_at,
            rl.address,
            rl.postal_code,
            rl.phone,
            rl.website_url,
            rl.reference_status,
            rl.location_description,
            rl.access_notes,
            rl.crowdsourced,
            rl.completeness_status
          FROM resource_locations rl
          JOIN public_data_sources pds ON pds.source_id = rl.source_id
          WHERE rl.kind = $1
          `,
        ];
        const params: Array<string | number> = [kind];

        if (kind === "facility") {
          queryParts.push("AND rl.source_id = 'mohserlo'");
        }

        if (province) {
          params.push(province);
          queryParts.push(`AND rl.province = $${params.length}`);
        }

        if (q) {
          params.push(`%${q}%`);
          const likeParamIndex = params.length;
          queryParts.push(`
            AND (
              rl.name ILIKE $${likeParamIndex}
              OR COALESCE(rl.city, '') ILIKE $${likeParamIndex}
              OR COALESCE(rl.address, '') ILIKE $${likeParamIndex}
              OR COALESCE(rl.location_description, '') ILIKE $${likeParamIndex}
              OR COALESCE(rl.access_notes, '') ILIKE $${likeParamIndex}
            )
          `);
        }

        queryParts.push("ORDER BY rl.name");

        const rows = (await sql.unsafe(
          queryParts.join("\n"),
          params,
        )) as ResourceRow[];

        const normalizedRows = rows
          .map((row) => mapResourceRecord(row, latitude, longitude))
          .filter((row) => {
            if (latitude === undefined || longitude === undefined) {
              return true;
            }
            return (row.distance_km ?? Number.POSITIVE_INFINITY) <= radius;
          })
          .sort((left, right) => {
            if (
              left.distance_km !== undefined &&
              right.distance_km !== undefined
            ) {
              return left.distance_km - right.distance_km;
            }
            if (kind === "facility") {
              if (q) {
                const facilityQueryRankDelta =
                  getFacilityQuerySortRank(left, q) -
                  getFacilityQuerySortRank(right, q);
                if (facilityQueryRankDelta !== 0) {
                  return facilityQueryRankDelta;
                }
              }
              const facilityRankDelta =
                getFacilitySortRank(left) - getFacilitySortRank(right);
              if (facilityRankDelta !== 0) {
                return facilityRankDelta;
              }
            }
            return left.name.localeCompare(right.name);
          });

        const displayRows =
          kind === "facility" &&
          latitude === undefined &&
          longitude === undefined &&
          !q
            ? dedupeDefaultFacilityRows(normalizedRows)
            : kind === "facility" && q
              ? dedupeFacilitySearchRows(normalizedRows, q)
              : normalizedRows;

        const limitedRows = displayRows
          .slice(0, limit);

        const sourceStatusRows = (await sql.unsafe(
          `
          SELECT
            source_id,
            source_name,
            provenance_url,
            domain,
            last_refreshed_at
          FROM public_data_sources
          WHERE domain = $1
          ORDER BY source_name
          `,
          [domain],
        )) as Array<{
          source_id: string;
          source_name: string;
          provenance_url: string;
          domain: "provider_facility" | "aed";
          last_refreshed_at: string | Date | null;
        }>;

        return {
          success: true as const,
          count: limitedRows.length,
          data: limitedRows,
          meta: {
            kind,
            query: {
              q,
              province,
              latitude,
              longitude,
              radius,
              limit,
            },
            source_status: buildSourceStatusRecords(sourceStatusRows),
          },
        };
      },
    );

    return NextResponse.json(payload, {
      headers: publicCacheHeaders(300, 900),
    });
  } catch (error) {
    logger.error("Failed to fetch resources", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch resources",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}

function mapResourceRecord(
  row: ResourceRow,
  latitude?: number,
  longitude?: number,
): ResourceRecord {
  const distanceKm =
    latitude !== undefined && longitude !== undefined
      ? calculateDistanceKm(latitude, longitude, row.latitude, row.longitude)
      : undefined;
  const freshnessState = deriveFreshnessState(
    row.kind === "facility" ? "provider_facility" : "aed",
    row.last_refreshed_at,
    row.provenance_url,
  );

  return {
    id: row.id,
    kind: row.kind,
    name: row.name,
    province: row.province,
    city: row.city,
    latitude: Number(row.latitude),
    longitude: Number(row.longitude),
    distance_km: distanceKm,
    source_id: row.source_id,
    source_name: row.source_name,
    provenance_url: row.provenance_url,
    last_refreshed_at:
      row.last_refreshed_at instanceof Date
        ? row.last_refreshed_at.toISOString()
        : row.last_refreshed_at
          ? new Date(row.last_refreshed_at).toISOString()
          : null,
    freshness_state: freshnessState,
    caveat_class:
      row.kind === "facility"
        ? "reference_directory"
        : "crowdsourced_incomplete",
    address: row.address,
    postal_code: row.postal_code,
    phone: row.phone,
    website_url: row.website_url,
    reference_status: row.reference_status ?? undefined,
    location_description: row.location_description,
    access_notes: row.access_notes,
    crowdsourced: row.kind === "aed" || row.crowdsourced ? true : undefined,
    completeness_status:
      row.kind === "aed"
        ? "incomplete"
        : (row.completeness_status ?? undefined),
  };
}

function getFacilitySortRank(resource: ResourceRecord): number {
  const text = [resource.name, resource.location_description]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (matchesKeywordGroup(text, EMERGENCY_FACILITY_KEYWORDS)) {
    return 0;
  }

  if (matchesKeywordGroup(text, COMMUNITY_FACILITY_KEYWORDS)) {
    return 1;
  }

  if (matchesKeywordGroup(text, PHARMACY_KEYWORDS)) {
    return 2;
  }

  let rank = matchesKeywordGroup(text, DIAGNOSTIC_FACILITY_KEYWORDS) ? 4 : 3;

  if (/^\d/.test(resource.name)) {
    rank += 2;
  }

  return rank;
}

function getFacilityQuerySortRank(
  resource: ResourceRecord,
  rawQuery: string,
): number {
  const query = normalizeSearchText(rawQuery);
  const queryTokens = tokenizeSearchQuery(rawQuery);

  if (!query || queryTokens.length === 0) {
    return 50;
  }

  const name = normalizeSearchText(resource.name);
  const city = normalizeSearchText(resource.city);
  const address = normalizeSearchText(resource.address);
  const locationDescription = normalizeSearchText(resource.location_description);
  const accessNotes = normalizeSearchText(resource.access_notes);
  const combined = [
    name,
    city,
    address,
    locationDescription,
    accessNotes,
  ]
    .filter(Boolean)
    .join(" ");

  if (name === query) {
    return 0;
  }

  if (name.startsWith(query)) {
    return 1;
  }

  if (queryTokens.every((token) => name.includes(token))) {
    return 2;
  }

  if (city === query || address === query) {
    return 3;
  }

  if (city.startsWith(query) || address.startsWith(query)) {
    return 4;
  }

  if (
    queryTokens.every((token) => city.includes(token)) ||
    queryTokens.every((token) => address.includes(token))
  ) {
    return 5;
  }

  if (
    queryTokens.every((token) => locationDescription.includes(token)) ||
    queryTokens.every((token) => accessNotes.includes(token))
  ) {
    return 6;
  }

  if (queryTokens.every((token) => combined.includes(token))) {
    return 7;
  }

  if (name.includes(query)) {
    return 8;
  }

  if (combined.includes(query)) {
    return 9;
  }

  return 10;
}

function matchesKeywordGroup(
  text: string,
  keywords: readonly string[],
): boolean {
  return keywords.some((keyword) => text.includes(keyword));
}

function dedupeDefaultFacilityRows(
  resources: ResourceRecord[],
): ResourceRecord[] {
  const seen = new Set<string>();
  const deduped: ResourceRecord[] = [];

  for (const resource of resources) {
    const key = buildFacilityDeduplicationKey(resource);
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    deduped.push(resource);
  }

  return deduped;
}

function dedupeFacilitySearchRows(
  resources: ResourceRecord[],
  rawQuery: string,
): ResourceRecord[] {
  const queryTokens = tokenizeSearchQuery(rawQuery);

  if (queryTokens.length < 2) {
    return resources;
  }

  const seen = new Set<string>();
  const deduped: ResourceRecord[] = [];

  for (const resource of resources) {
    const key = buildFacilitySearchDeduplicationKey(resource, queryTokens);
    if (key && seen.has(key)) {
      continue;
    }

    if (key) {
      seen.add(key);
    }

    deduped.push(resource);
  }

  return deduped;
}

function buildFacilityDeduplicationKey(resource: ResourceRecord): string {
  return [
    normalizeDeduplicationPart(resource.name),
    normalizeDeduplicationPart(resource.address),
    normalizeDeduplicationPart(resource.city),
  ].join("|");
}

function buildFacilitySearchDeduplicationKey(
  resource: ResourceRecord,
  queryTokens: string[],
): string | null {
  const normalizedName = normalizeSearchText(resource.name);

  if (!queryTokens.every((token) => normalizedName.includes(token))) {
    return null;
  }

  return [
    resource.source_id,
    normalizeDeduplicationPart(resource.city),
    roundCoordinateForGrouping(resource.latitude),
    roundCoordinateForGrouping(resource.longitude),
    queryTokens.join(" "),
  ].join("|");
}

function normalizeDeduplicationPart(value: string | null | undefined): string {
  return (value ?? "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function normalizeSearchText(value: string | null | undefined): string {
  return (value ?? "")
    .toLowerCase()
    .replace(QUERY_TOKEN_SEPARATOR, " ")
    .trim();
}

function tokenizeSearchQuery(value: string): string[] {
  return normalizeSearchText(value)
    .split(" ")
    .filter(Boolean);
}

function roundCoordinateForGrouping(value: number): string {
  return value.toFixed(2);
}
