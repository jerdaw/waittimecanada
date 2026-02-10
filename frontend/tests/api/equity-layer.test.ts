import { describe, expect, it } from "vitest";
import { GET } from "@/app/api/equity-layer/route";

describe("Equity Layer API", () => {
  it("returns ON placeholder layer by default", async () => {
    const request = new Request("http://localhost/api/equity-layer");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.metadata.province).toBe("ON");
    expect(json.metadata.is_placeholder).toBe(true);
    expect(json.data.type).toBe("FeatureCollection");
    expect(json.data.features.length).toBeGreaterThan(0);
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
