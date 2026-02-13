import { describe, expect, it } from "vitest";
import { GET } from "@/app/api/equity-layer/route";

describe("Equity Layer API", () => {
  it("returns ON equity layer by default", async () => {
    const request = new Request("http://localhost/api/equity-layer");
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.success).toBe(true);
    expect(json.metadata.province).toBe("ON");
    // is_placeholder depends on whether file exists - both true and false are valid
    expect(typeof json.metadata.is_placeholder).toBe("boolean");
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
