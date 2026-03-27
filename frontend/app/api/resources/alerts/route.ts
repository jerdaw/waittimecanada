import { NextRequest, NextResponse } from "next/server";

import { publicCacheHeaders } from "@/utils/cache";
import { getDb } from "@/utils/db";
import { logger } from "@/utils/logger";
import {
  buildSourceStatusRecords,
  deriveFreshnessState,
  type AlertRecord,
  type SourceStatusRecord,
} from "@/utils/public-health-hub";
import { checkRateLimit } from "@/utils/rate-limit";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";
import { ResourceAlertsQuerySchema } from "@/utils/validations";

type AlertRow = {
  id: string;
  title: string;
  summary: string;
  alert_type: string;
  published_at: string | Date;
  source_updated_at: string | Date | null;
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | Date | null;
  affected_products: Array<{
    brand_name: string;
    din?: string | null;
  }> | null;
};

const ALERTS_CACHE_TTL_MS = 300_000;
const DPD_CACHE_TTL_MS = 86_400_000;
const DPD_API_URL = "https://health-products.canada.ca/api/drug/drugproduct/";
const DPD_PROVENANCE_URL =
  "https://health-products.canada.ca/api/documentation/dpd-documentation-en.html";
const DPD_SOURCE_STATUS = {
  source_id: "health-canada-dpd",
  source_name: "Drug Product Database (DPD)",
  provenance_url: DPD_PROVENANCE_URL,
} as const;

export async function GET(request: NextRequest) {
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) return rateLimitResponse;

  try {
    const { searchParams } = new URL(request.url);
    const rawParams = Object.fromEntries(searchParams.entries());
    const validation = ResourceAlertsQuerySchema.safeParse(rawParams);

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

    const { limit } = validation.data;

    const payload = await getOrSetServerCache(
      buildServerCacheKey("api:resources:alerts", { limit }),
      ALERTS_CACHE_TTL_MS,
      async () => {
        const sql = getDb();

        const rows = (await sql.unsafe(
          `
          SELECT
            pha.id,
            pha.title,
            pha.summary,
            pha.alert_type,
            pha.published_at,
            pha.source_updated_at,
            pha.source_id,
            pds.source_name,
            COALESCE(pha.provenance_url, pds.provenance_url) AS provenance_url,
            COALESCE(pha.last_refreshed_at, pds.last_refreshed_at) AS last_refreshed_at,
            pha.affected_products
          FROM public_health_alerts pha
          JOIN public_data_sources pds ON pds.source_id = pha.source_id
          ORDER BY pha.published_at DESC
          LIMIT $1
          `,
          [limit],
        )) as AlertRow[];

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
          ["safety_alert"],
        )) as Array<{
          source_id: string;
          source_name: string;
          provenance_url: string;
          domain: "safety_alert";
          last_refreshed_at: string | Date | null;
        }>;

        const dpdEnrichment = await enrichAlertsWithDPD(rows);

        return {
          success: true as const,
          count: dpdEnrichment.rows.length,
          data: dpdEnrichment.rows.map(mapAlertRecord),
          meta: {
            limit,
            source_status: buildAlertsSourceStatus(
              sourceStatusRows,
              dpdEnrichment.sourceStatus,
            ),
          },
        };
      },
    );

    return NextResponse.json(payload, {
      headers: publicCacheHeaders(300, 900),
    });
  } catch (error) {
    logger.error("Failed to fetch alerts", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch alerts",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}

function buildAlertsSourceStatus(
  sourceStatusRows: Array<{
    source_id: string;
    source_name: string;
    provenance_url: string;
    domain: "safety_alert";
    last_refreshed_at: string | Date | null;
  }>,
  dpdSourceStatus: SourceStatusRecord | null,
): SourceStatusRecord[] {
  const baseStatus = buildSourceStatusRecords(sourceStatusRows);
  return dpdSourceStatus ? [...baseStatus, dpdSourceStatus] : baseStatus;
}

async function enrichAlertsWithDPD(rows: AlertRow[]): Promise<{
  rows: AlertRow[];
  sourceStatus: SourceStatusRecord | null;
}> {
  let usedDPD = false;

  const enrichedRows = await Promise.all(
    rows.map(async (row) => {
      if (!isDrugAlert(row) || !row.affected_products?.length) {
        return row;
      }

      let rowUsedDPD = false;
      const affectedProducts = await Promise.all(
        row.affected_products.map(async (product) => {
          if (product.din || !product.brand_name) {
            return product;
          }

          rowUsedDPD = true;
          const enrichedProduct = await lookupDrugProductByBrandName(product.brand_name);
          if (!enrichedProduct?.din) {
            return product;
          }

          return {
            ...product,
            din: enrichedProduct.din,
          };
        }),
      );

      if (rowUsedDPD) {
        usedDPD = true;
      }

      return {
        ...row,
        affected_products: affectedProducts,
      };
    }),
  );

  return {
    rows: enrichedRows,
    sourceStatus: usedDPD
      ? {
          ...DPD_SOURCE_STATUS,
          last_refreshed_at: new Date().toISOString(),
          freshness_state: deriveFreshnessState(
            "health_product_reference",
            new Date().toISOString(),
            DPD_PROVENANCE_URL,
          ),
        }
      : null,
  };
}

function isDrugAlert(row: AlertRow): boolean {
  return row.alert_type.toLowerCase().includes("drug");
}

async function lookupDrugProductByBrandName(
  brandName: string,
): Promise<{ brand_name: string; din: string | null } | null> {
  const normalizedBrandName = brandName.trim();
  if (!normalizedBrandName) {
    return null;
  }

  const cached = await getOrSetServerCache(
    buildServerCacheKey("api:resources:alerts:dpd", {
      brand_name: normalizedBrandName.toLowerCase(),
    }),
    DPD_CACHE_TTL_MS,
    async () => {
      try {
        const response = await fetch(
          `${DPD_API_URL}?lang=en&type=json&brandname=${encodeURIComponent(normalizedBrandName)}`,
          {
            headers: {
              Accept: "application/json",
            },
            next: {
              revalidate: 86_400,
            },
          },
        );

        if (!response.ok) {
          return { product: null };
        }

        const payload = (await response.json()) as Array<{
          brand_name?: string;
          drug_identification_number?: string;
        }> | null;

        if (!Array.isArray(payload) || payload.length === 0) {
          return { product: null };
        }

        const exactMatch =
          payload.find(
            (item) =>
              item.brand_name?.trim().toLowerCase() ===
              normalizedBrandName.toLowerCase(),
          ) ?? payload[0];

        if (!exactMatch?.brand_name) {
          return { product: null };
        }

        return {
          product: {
            brand_name: exactMatch.brand_name,
            din: exactMatch.drug_identification_number ?? null,
          },
        };
      } catch (error) {
        logger.warn("DPD enrichment lookup failed", {
          brandName: normalizedBrandName,
          error: error instanceof Error ? error.message : "Unknown error",
        });
        return { product: null };
      }
    },
  );

  return cached.product;
}

function mapAlertRecord(row: AlertRow): AlertRecord {
  return {
    id: row.id,
    title: row.title,
    summary: row.summary,
    alert_type: row.alert_type,
    published_at: new Date(row.published_at).toISOString(),
    updated_at: row.source_updated_at
      ? new Date(row.source_updated_at).toISOString()
      : null,
    source_id: row.source_id,
    source_name: row.source_name,
    provenance_url: row.provenance_url,
    last_refreshed_at: row.last_refreshed_at
      ? new Date(row.last_refreshed_at).toISOString()
      : null,
    freshness_state: deriveFreshnessState(
      "safety_alert",
      row.last_refreshed_at,
      row.provenance_url,
    ),
    caveat_class: "official_alert_feed",
    affected_products: row.affected_products ?? [],
  };
}
