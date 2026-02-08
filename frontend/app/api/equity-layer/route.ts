import { NextResponse } from "next/server";
import {
  buildPlaceholderEquityFeatureCollection,
  type EquityLayerApiResponse,
} from "@/utils/equity";
import { publicCacheHeaders } from "@/utils/cache";

const SUPPORTED_PROVINCES = new Set(["ON"]);

function normalizeProvince(province: string | null): string {
  return (province ?? "ON").trim().toUpperCase();
}

export async function GET(request: Request) {
  const province = normalizeProvince(new URL(request.url).searchParams.get("province"));

  if (!SUPPORTED_PROVINCES.has(province)) {
    const response: EquityLayerApiResponse = {
      success: false,
      error: `Equity layer is not scaffolded for province ${province}`,
      setup_required: true,
      setup_steps: [
        "Add census tract boundaries for the province (StatsCan 2021)",
        "Join tract boundaries to income variables and derive quintiles",
        "Replace placeholder payload in /api/equity-layer with processed dataset",
      ],
    };
    return NextResponse.json(response, { status: 404 });
  }

  const response: EquityLayerApiResponse = {
    success: true,
    data: buildPlaceholderEquityFeatureCollection(province),
    metadata: {
      province,
      source: "WaitTime Canada placeholder scaffold",
      attribution: "Placeholder geometry only; replace with Statistics Canada Census tract data",
      generated_at: new Date().toISOString(),
      is_placeholder: true,
      note: "This layer validates toggle + legend + API plumbing until census integration is complete.",
    },
  };

  return NextResponse.json(response, {
    status: 200,
    headers: publicCacheHeaders(3600, 10800),
  });
}
