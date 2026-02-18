import { describe, expect, it } from "vitest";
import { constants, promises as fs } from "fs";
import path from "path";
import { GET } from "@/app/api/equity-layer/route";

async function optimizedLayerExists(): Promise<boolean> {
  const candidates = [
    path.join(
      process.cwd(),
      "backend",
      "data",
      "layers",
      "ontario-equity-layer.optimized.geojson",
    ),
    path.join(
      process.cwd(),
      "..",
      "backend",
      "data",
      "layers",
      "ontario-equity-layer.optimized.geojson",
    ),
  ];
  for (const candidate of candidates) {
    try {
      await fs.access(candidate, constants.F_OK);
      return true;
    } catch {
      // continue
    }
  }
  return false;
}

describe("Equity Layer API", () => {
  it("returns ON equity layer by default", async () => {
    const hasOptimizedLayer = await optimizedLayerExists();
    const request = new Request("http://localhost/api/equity-layer");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.metadata.province).toBe("ON");
    // is_placeholder depends on whether file exists - both true and false are valid
    expect(typeof json.metadata.is_placeholder).toBe("boolean");
    expect(json.metadata.reference_year).toBe(2021);
    expect(json.metadata.causal_inference).toBe(false);
    expect(typeof json.metadata.source_file).toBe("string");
    if (hasOptimizedLayer) {
      expect(json.metadata.source_file).toBe(
        "ontario-equity-layer.optimized.geojson",
      );
      expect(json.metadata.optimized_geometry).toBe(true);
    }
    if (json.success) {
      expect(json.data.type).toBe("FeatureCollection");
      expect(Array.isArray(json.data.features)).toBe(true);
    }
  });

  it("normalizes lowercase province query", async () => {
    const request = new Request(
      "http://localhost/api/equity-layer?province=on",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.metadata.province).toBe("ON");
  });

  it("returns setup instructions for unsupported provinces", async () => {
    const request = new Request(
      "http://localhost/api/equity-layer?province=QC",
    );
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(404);
    expect(json.success).toBe(false);
    expect(json.setup_required).toBe(true);
    expect(Array.isArray(json.setup_steps)).toBe(true);
  });
});
