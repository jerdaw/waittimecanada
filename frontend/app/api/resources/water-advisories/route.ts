import { NextRequest, NextResponse } from "next/server";

import { publicCacheHeaders } from "@/utils/cache";
import { logger } from "@/utils/logger";
import {
  type FreshnessState,
  type SourceCatalogRecord,
  type SourceStatusRecord,
  type WaterAdvisoryRecord,
} from "@/utils/public-health-hub";
import { checkRateLimit } from "@/utils/rate-limit";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import { ResourceWaterAdvisoriesQuerySchema } from "@/utils/validations";

const DAY_MS = 24 * 60 * 60 * 1000;
const WATER_ADVISORIES_CACHE_TTL_MS = 3_600_000;
const WATER_ADVISORIES_DATA_URL =
  "https://www.sac-isc.gc.ca/DAM/DAM-ISC-SAC/DAM-WTR/STAGING/texte-text/lTDWA_map_data_1572010201618_eng.txt";
const WATER_ADVISORIES_PROVENANCE_URL =
  "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679";
const WATER_ADVISORIES_SOURCE_NAME =
  "ISC Long-term Drinking Water Advisories";
const WATER_ADVISORIES_SCOPE_NOTE =
  "Long-term drinking water advisories are currently surfaced for Ontario reserve systems only.";
const WATER_ADVISORIES_SOURCE_CATALOG = {
  source_id: "isc-drinking-water-advisories",
  domain: "environmental_overlay",
  source_name: WATER_ADVISORIES_SOURCE_NAME,
  connector_type: "file_download",
  access_route: "ISC map data JSON export",
  license_reuse_status: "approved_with_conditions",
  attribution_requirement: "Keep Indigenous Services Canada provenance visible.",
  update_cadence: "periodic",
  recommended_usage_mode: "scheduled_ingest",
  public_methodology_note:
    "Official ISC data on active long-term drinking water advisories for public systems on reserve in Ontario. This is not a complete map of all Ontario drinking water advisories.",
  provenance_url: WATER_ADVISORIES_PROVENANCE_URL,
  last_verified_at: "2026-04-23",
} as const;

type WaterAdvisoriesScopeMetadata = {
  mode: "ontario_only";
  available_provinces: ["ON"];
  requested_province: string;
  note: string;
};

type RawCommunityRecord = {
  CommunityName?: string;
  Province?: string;
  ProvinceAcronym?: string;
  Latitude?: string | number;
  Longitude?: string | number;
  LTDWACurrent?: RawAdvisoryRecord[];
};

type RawAdvisoryRecord = {
  AdvisoryID?: string;
  WaterSystemName?: string;
  AdvisoryType?: string;
  DateSet?: string;
  DateLTDWASet?: string;
  DateExpected?: string;
  PopulatioEstimated?: string;
  CorrectiveMeasure?: string;
  LongPhase?: string;
  Lattitude?: string | number;
  Longitude?: string | number;
};

type RawPayload = {
  data?: RawCommunityRecord[];
  GenerateDate?: string;
};

export async function GET(request: NextRequest) {
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());
    const validation = ResourceWaterAdvisoriesQuerySchema.safeParse(rawParams);

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

    const { province, q, limit } = validation.data;
    const scope: WaterAdvisoriesScopeMetadata = {
      mode: "ontario_only",
      available_provinces: ["ON"],
      requested_province: province,
      note: WATER_ADVISORIES_SCOPE_NOTE,
    };

    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:resources:water-advisories", {
        province,
        q: q ?? null,
        limit,
      }),
      WATER_ADVISORIES_CACHE_TTL_MS,
      async () => {
        if (province !== "ON") {
          return {
            success: true as const,
            count: 0,
            data: [],
            meta: {
              query: { province, q, limit },
              scope,
              summary: {
                active_advisories: 0,
                affected_communities: 0,
              },
              source_status: [],
              source_catalog: [],
            },
          };
        }

        const response = await fetch(WATER_ADVISORIES_DATA_URL, {
          headers: {
            Accept: "application/json, text/plain",
          },
          next: {
            revalidate: 3600,
          },
        });

        if (!response.ok) {
          throw new Error(
            `ISC drinking water advisories request failed with ${response.status}`,
          );
        }

        const json = (await response.json()) as RawPayload;
        const lastRefreshedAt = toGeneratedTimestamp(json.GenerateDate);
        const sourceStatus: SourceStatusRecord = {
          source_id: WATER_ADVISORIES_SOURCE_CATALOG.source_id,
          source_name: WATER_ADVISORIES_SOURCE_NAME,
          provenance_url: WATER_ADVISORIES_PROVENANCE_URL,
          last_refreshed_at: lastRefreshedAt,
          freshness_state: deriveWaterAdvisoryFreshnessState(lastRefreshedAt),
        };

        const ontarioRows = flattenOntarioWaterAdvisories(
          json.data ?? [],
          lastRefreshedAt,
        );
        const filteredRows = filterWaterAdvisories(ontarioRows, q);
        const visibleRows =
          sourceStatus.freshness_state === "suppress"
            ? []
            : filteredRows.slice(0, limit);

        return {
          success: true as const,
          count: visibleRows.length,
          data: visibleRows,
          meta: {
            query: { province, q, limit },
            scope,
            summary: {
              active_advisories: ontarioRows.length,
              affected_communities: new Set(
                ontarioRows.map((row) => row.community_name),
              ).size,
            },
            source_status: [sourceStatus],
            source_catalog: [
              buildWaterAdvisoriesSourceCatalogRecord(sourceStatus),
            ] satisfies SourceCatalogRecord[],
          },
        };
      },
    );

    return NextResponse.json(payload, {
      headers: publicCacheHeaders(3600, 14_400),
    });
  } catch (error) {
    logger.error("Failed to fetch drinking water advisories", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch drinking water advisories",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}

function buildWaterAdvisoriesSourceCatalogRecord(
  sourceStatus: SourceStatusRecord,
): SourceCatalogRecord {
  return {
    ...WATER_ADVISORIES_SOURCE_CATALOG,
    last_refreshed_at: sourceStatus.last_refreshed_at,
    freshness_state: sourceStatus.freshness_state,
  };
}

function flattenOntarioWaterAdvisories(
  rows: RawCommunityRecord[],
  lastRefreshedAt: string | null,
): WaterAdvisoryRecord[] {
  const advisories: WaterAdvisoryRecord[] = [];

  for (const community of rows) {
    if (community.ProvinceAcronym !== "ON" && community.Province !== "Ontario") {
      continue;
    }

    const active = community.LTDWACurrent ?? [];
    for (const advisory of active) {
      const latitude = toNumber(advisory.Lattitude ?? community.Latitude);
      const longitude = toNumber(advisory.Longitude ?? community.Longitude);
      if (latitude === null || longitude === null) {
        continue;
      }

      const id = String(advisory.AdvisoryID ?? "").trim();
      const communityName = String(community.CommunityName ?? "").trim();
      const waterSystemName = String(advisory.WaterSystemName ?? "").trim();
      const advisoryType = String(advisory.AdvisoryType ?? "").trim();
      const advisorySetAt = toIsoDate(advisory.DateSet);
      const longTermSince = toIsoDate(advisory.DateLTDWASet);

      if (!id || !communityName || !waterSystemName || !advisoryType) {
        continue;
      }
      if (!advisorySetAt || !longTermSince) {
        continue;
      }

      advisories.push({
        id: `isc-drinking-water-advisories-${id}`,
        community_name: communityName,
        water_system_name: waterSystemName,
        advisory_type: advisoryType,
        advisory_set_at: advisorySetAt,
        long_term_since: longTermSince,
        projected_lift_date: toIsoDate(advisory.DateExpected),
        population_estimate: cleanString(advisory.PopulatioEstimated),
        corrective_measure: cleanString(advisory.CorrectiveMeasure),
        project_phase: cleanString(advisory.LongPhase),
        latitude,
        longitude,
        source_id: WATER_ADVISORIES_SOURCE_CATALOG.source_id,
        source_name: WATER_ADVISORIES_SOURCE_NAME,
        provenance_url: WATER_ADVISORIES_PROVENANCE_URL,
        last_refreshed_at: lastRefreshedAt,
        freshness_state: deriveWaterAdvisoryFreshnessState(lastRefreshedAt),
        caveat_class: "official_environmental_advisory",
      });
    }
  }

  advisories.sort((left, right) => {
    const dateCompare =
      new Date(left.long_term_since).getTime() -
      new Date(right.long_term_since).getTime();
    if (dateCompare !== 0) {
      return dateCompare;
    }

    return left.community_name.localeCompare(right.community_name);
  });

  return advisories;
}

function filterWaterAdvisories(
  rows: WaterAdvisoryRecord[],
  query: string | undefined,
) {
  if (!query) {
    return rows;
  }

  const normalizedQuery = query.trim().toLowerCase();
  return rows.filter((row) =>
    [
      row.community_name,
      row.water_system_name,
      row.advisory_type,
      row.population_estimate,
      row.project_phase,
      row.corrective_measure,
    ]
      .filter(Boolean)
      .some((value) => value!.toLowerCase().includes(normalizedQuery)),
  );
}

function deriveWaterAdvisoryFreshnessState(
  lastRefreshedAt: string | null,
): FreshnessState {
  if (!lastRefreshedAt) {
    return "suppress";
  }

  const ageMs = Date.now() - new Date(lastRefreshedAt).getTime();
  if (ageMs <= 7 * DAY_MS) {
    return "show";
  }
  if (ageMs <= 30 * DAY_MS) {
    return "warn";
  }
  return "suppress";
}

function toGeneratedTimestamp(value: string | undefined): string | null {
  if (!value) {
    return null;
  }

  return toIsoDate(`${value}T00:00:00.000Z`);
}

function toIsoDate(value: string | undefined): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed.toISOString();
}

function toNumber(value: string | number | undefined): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function cleanString(value: string | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}
