import { NextResponse } from "next/server";
import { publicCacheHeaders } from "@/utils/cache";
import {
  isSupportedEquityProvince,
  loadEquityLayerForProvinceWithSource,
} from "@/utils/equityLayerData";

function normalizeProvince(province: string | null): string {
  return (province ?? "ON").trim().toUpperCase();
}

export async function GET(request: Request) {
  const province = normalizeProvince(
    new URL(request.url).searchParams.get("province"),
  );

  if (!isSupportedEquityProvince(province)) {
    return NextResponse.json(
      {
        success: false,
        error: `Equity layer is not scaffolded for province ${province}`,
        setup_required: true,
        setup_steps: [
          "Acquire Statistics Canada census tract data for province",
          "Process GeoJSON with income quantile fields",
          "Place processed layer in backend/data/layers/",
          "Update SUPPORTED_PROVINCES in equity-layer API route",
        ],
      },
      { status: 404 },
    );
  }

  try {
    const { data: geojson, source_file } =
      await loadEquityLayerForProvinceWithSource(province);
    const isPlaceholder = geojson.features.some(
      (feature) => feature.properties.is_placeholder,
    );
    const usingOptimizedLayer = source_file.includes(".optimized.");

    return NextResponse.json(
      {
        success: true,
        data: geojson,
        metadata: {
          province,
          source: isPlaceholder
            ? "Scaffold placeholder tract dataset"
            : "Statistics Canada 2021 Census (Processed)",
          attribution:
            "Contains information licensed under the Open Government Licence – Canada.",
          generated_at: new Date().toISOString(),
          is_placeholder: isPlaceholder,
          source_file,
          optimized_geometry: usingOptimizedLayer,
          reference_year: 2021,
          interpretation: "descriptive_context_layer_only",
          causal_inference: false,
          temporal_alignment_note:
            "Income values are from the 2021 Census; wait times are recent aggregates and may not be temporally aligned.",
          note: isPlaceholder
            ? "Placeholder tract layer loaded. Replace with processed Ontario census tract file."
            : usingOptimizedLayer
              ? "Ontario optimized layer loaded from Statistics Canada 2021 census tract data for descriptive equity context only."
              : "Ontario canonical layer loaded from Statistics Canada 2021 census tract data for descriptive equity context only.",
        },
      },
      {
        status: 200,
        headers: publicCacheHeaders(3600, 86400),
      },
    );
  } catch (error) {
    console.error("Failed to serve equity layer:", error);
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error";
    if (errorMessage.includes("not found")) {
      return NextResponse.json(
        {
          success: false,
          error: "Equity layer data not found (run preparation script)",
          setup_required: true,
          setup_steps: [
            "Run backend/scripts/prepare_equity_layer.py with Ontario inputs",
            "Verify backend/data/layers/ontario-equity-layer.geojson exists",
          ],
        },
        { status: 404 },
      );
    }
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 },
    );
  }
}
