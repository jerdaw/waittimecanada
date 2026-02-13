import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { publicCacheHeaders } from "@/utils/cache";

const SUPPORTED_PROVINCES = new Set(["ON"]);

function normalizeProvince(province: string | null): string {
  return (province ?? "ON").trim().toUpperCase();
}

export async function GET(request: Request) {
  const province = normalizeProvince(
    new URL(request.url).searchParams.get("province"),
  );

  if (!SUPPORTED_PROVINCES.has(province)) {
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
    // Determine path to the GeoJSON layer
    // In production, this data should be in a known location
    const dataPath = path.join(
      process.cwd(),
      "..",
      "backend",
      "data",
      "layers",
      "ontario-equity-layer.geojson",
    );

    // Check if file exists
    try {
      await fs.access(dataPath);
    } catch {
      return NextResponse.json(
        {
          success: false,
          error: "Equity layer data not found (run preparation script)",
          setup_required: true,
          setup_steps: [
            "Run backend data preparation script",
            "Verify GeoJSON layer generated in backend/data/layers/",
          ],
        },
        { status: 404 },
      );
    }

    const fileContents = await fs.readFile(dataPath, "utf-8");
    const geojson = JSON.parse(fileContents);

    return NextResponse.json(
      {
        success: true,
        data: geojson,
        metadata: {
          province,
          source: "Statistics Canada 2021 Census (Processed)",
          attribution:
            "Contains information licensed under the Open Government Licence – Canada.",
          generated_at: new Date().toISOString(),
          is_placeholder: false,
        },
      },
      {
        status: 200,
        headers: publicCacheHeaders(3600, 86400),
      },
    );
  } catch (error) {
    console.error("Failed to serve equity layer:", error);
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 },
    );
  }
}
