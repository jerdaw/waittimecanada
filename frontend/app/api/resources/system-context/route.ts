import { NextRequest, NextResponse } from "next/server";

import { NO_STORE_HEADERS, publicCacheHeaders } from "@/utils/cache";
import { getDb } from "@/utils/db";
import { logger } from "@/utils/logger";
import {
  buildSourceCatalogRecords,
  buildSourceStatusRecords,
  deriveFreshnessState,
  type SourceCatalogRecord,
  type SystemContextDispatchCentreRecord,
  type SystemContextParamedicServiceRecord,
} from "@/utils/public-health-hub";
import { checkRateLimit } from "@/utils/rate-limit";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import { ResourceSystemContextQuerySchema } from "@/utils/validations";

type SystemMetricRow = {
  id: string;
  source_id: string;
  series_key:
    | "cacc_average_response_times"
    | "paramedic_service_response_performance";
  province: string;
  geography_type: string;
  geography_name: string;
  reporting_year: number;
  dimension_label: string | null;
  metrics: Record<string, string | number | null>;
  provenance_url: string;
  last_refreshed_at: string | Date | null;
  source_name: string;
};

type SourceCatalogRow = {
  source_id: string;
  source_name: string;
  provenance_url: string;
  domain: "system_context";
  connector_type: string;
  access_route: string;
  license_reuse_status: string;
  attribution_requirement: string;
  update_cadence: string;
  recommended_usage_mode: string;
  public_methodology_note: string | null;
  last_verified_at: string | Date | null;
  last_refreshed_at: string | Date | null;
};

type ResourcesScopeMetadata = {
  mode: "ontario_only";
  available_provinces: ["ON"];
  requested_province: string;
  note: string;
};

const SYSTEM_CONTEXT_CACHE_TTL_MS = 300_000;
const SYSTEM_CONTEXT_SCOPE_NOTE =
  "Ontario system-context reporting is currently shipped for Ontario only.";
const EMS_SOURCE_ID = "ontario-land-ambulance-response-times";

export async function GET(request: NextRequest) {
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());
    const validation = ResourceSystemContextQuerySchema.safeParse(rawParams);

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

    const { province, q, limit } = validation.data;
    const scope: ResourcesScopeMetadata = {
      mode: "ontario_only",
      available_provinces: ["ON"],
      requested_province: province,
      note: SYSTEM_CONTEXT_SCOPE_NOTE,
    };

    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:resources:system-context", {
        province,
        q: q ?? null,
        limit,
      }),
      SYSTEM_CONTEXT_CACHE_TTL_MS,
      async () => {
        if (province !== "ON") {
          return {
            success: true as const,
            data: {
              dispatch_centres: [],
              paramedic_services: [],
            },
            meta: {
              query: { province, q, limit },
              scope,
              source_status: [],
              source_catalog: [],
            },
          };
        }

        const sql = getDb();
        const params: Array<string | number> = [EMS_SOURCE_ID];
        let searchFilter = "";

        if (q) {
          params.push(`%${q}%`);
          searchFilter = `AND sm.geography_name ILIKE $${params.length}`;
        }

        const dispatchParams: Array<string | number> = [...params, limit];
        const dispatchRows = (await sql.unsafe(
          `
          SELECT
            sm.id,
            sm.source_id,
            sm.series_key,
            sm.province,
            sm.geography_type,
            sm.geography_name,
            sm.reporting_year,
            sm.dimension_label,
            sm.metrics,
            sm.provenance_url,
            sm.last_refreshed_at,
            pds.source_name
          FROM public_health_system_metrics sm
          JOIN public_data_sources pds ON pds.source_id = sm.source_id
          WHERE sm.source_id = $1
            AND sm.series_key = 'cacc_average_response_times'
            ${searchFilter}
          ORDER BY sm.geography_name ASC, sm.reporting_year DESC
          LIMIT $${dispatchParams.length}
          `,
          dispatchParams,
        )) as SystemMetricRow[];

        const paramedicRows = (await sql.unsafe(
          `
          SELECT
            sm.id,
            sm.source_id,
            sm.series_key,
            sm.province,
            sm.geography_type,
            sm.geography_name,
            sm.reporting_year,
            sm.dimension_label,
            sm.metrics,
            sm.provenance_url,
            sm.last_refreshed_at,
            pds.source_name
          FROM public_health_system_metrics sm
          JOIN public_data_sources pds ON pds.source_id = sm.source_id
          WHERE sm.source_id = $1
            AND sm.series_key = 'paramedic_service_response_performance'
            ${searchFilter}
          ORDER BY sm.geography_name ASC, sm.reporting_year DESC, sm.dimension_label NULLS FIRST
          `,
          params,
        )) as SystemMetricRow[];

        const sourceCatalogRows = (await sql.unsafe(
          `
          SELECT
            source_id,
            source_name,
            provenance_url,
            domain,
            connector_type,
            access_route,
            license_reuse_status,
            attribution_requirement,
            update_cadence,
            recommended_usage_mode,
            public_methodology_note,
            last_verified_at,
            last_refreshed_at
          FROM public_data_sources
          WHERE source_id = $1
          `,
          [EMS_SOURCE_ID],
        )) as SourceCatalogRow[];

        const sourceStatus = buildSourceStatusRecords(sourceCatalogRows);
        const sourceCatalog = buildSourceCatalogRecords(sourceCatalogRows);
        const sourceFreshnessState =
          sourceStatus[0]?.freshness_state ?? "suppress";
        const dispatchCentres =
          sourceFreshnessState === "suppress"
            ? []
            : dispatchRows.map(mapDispatchCentreRecord);
        const paramedicServices =
          sourceFreshnessState === "suppress"
            ? []
            : mapParamedicServiceRecords(paramedicRows, limit);

        return {
          success: true as const,
          data: {
            dispatch_centres: dispatchCentres,
            paramedic_services: paramedicServices,
          },
          meta: {
            query: { province, q, limit },
            scope,
            source_status: sourceStatus,
            source_catalog: sourceCatalog,
          },
        };
      },
    );

    return NextResponse.json(payload, {
      headers: publicCacheHeaders(300, 900),
    });
  } catch (error) {
    logger.error("Failed to fetch system context", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch system context",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}

function mapDispatchCentreRecord(
  row: SystemMetricRow,
): SystemContextDispatchCentreRecord {
  return {
    id: row.id,
    geography_name: row.geography_name,
    reporting_year: Number(row.reporting_year),
    average_response_time_minutes: toNullableNumber(
      row.metrics.average_response_time_minutes,
    ),
    call_volume: toNullableNumber(row.metrics.call_volume),
    source_id: row.source_id,
    source_name: row.source_name,
    provenance_url: row.provenance_url,
    last_refreshed_at: toIsoTimestamp(row.last_refreshed_at),
    freshness_state: deriveFreshnessState(
      "system_context",
      row.last_refreshed_at,
      row.provenance_url,
    ),
    caveat_class: "official_system_context",
  };
}

function mapParamedicServiceRecords(
  rows: SystemMetricRow[],
  limit: number,
): SystemContextParamedicServiceRecord[] {
  const grouped = new Map<string, SystemContextParamedicServiceRecord>();

  for (const row of rows) {
    const key = `${row.geography_name}|${row.reporting_year}`;
    const existing = grouped.get(key);

    if (!existing) {
      if (grouped.size >= limit) {
        continue;
      }

      grouped.set(key, {
        id: row.id,
        geography_name: row.geography_name,
        reporting_year: Number(row.reporting_year),
        severity_breakdown: [],
        source_id: row.source_id,
        source_name: row.source_name,
        provenance_url: row.provenance_url,
        last_refreshed_at: toIsoTimestamp(row.last_refreshed_at),
        freshness_state: deriveFreshnessState(
          "system_context",
          row.last_refreshed_at,
          row.provenance_url,
        ),
        caveat_class: "official_system_context",
      });
    }

    grouped.get(key)?.severity_breakdown.push({
      patient_severity: row.dimension_label,
      response_time_plan_minutes: toNullableNumber(
        row.metrics.response_time_plan_minutes,
      ),
      planned_response_pct: toNullableNumber(row.metrics.planned_response_pct),
      performance_pct: toNullableNumber(row.metrics.performance_pct),
    });
  }

  return Array.from(grouped.values());
}

function toNullableNumber(
  value: string | number | null | undefined,
): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function toIsoTimestamp(
  value: string | Date | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  return value instanceof Date
    ? value.toISOString()
    : new Date(value).toISOString();
}
