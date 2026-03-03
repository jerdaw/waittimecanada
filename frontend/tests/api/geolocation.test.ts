import { describe, expect, test, vi } from "vitest";
import { GET } from "../../app/api/geolocation/route";
import { NextRequest } from "next/server";

describe("Geolocation API", () => {
  const originalFetch = global.fetch;

  beforeAll(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            latitude: 43.6532,
            longitude: -79.3832,
            city: "Toronto",
            region: "Ontario",
            country_name: "CA",
          }),
      } as Response),
    );
  });

  afterAll(() => {
    global.fetch = originalFetch;
  });

  test("GET /api/geolocation uses x-forwarded-for header", async () => {
    const req = new NextRequest("http://localhost:3000/api/geolocation", {
      headers: {
        "x-forwarded-for": "8.8.8.8",
        "x-vercel-ip-city": "Toronto",
        "x-vercel-ip-country": "CA",
        "x-vercel-ip-latitude": "43.6532",
        "x-vercel-ip-longitude": "-79.3832",
        "x-vercel-ip-timezone": "America/Toronto",
      },
    });
    const res = await GET(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    console.log("Geolocation API response:", JSON.stringify(data, null, 2));

    // The API returns { success: true, location: { ... } }
    expect(data.location).toBeDefined();
    expect(data.location.city).toBe("Toronto");
    expect(data.location.country).toBe("CA");
  });

  test("GET /api/geolocation handles missing headers gracefully", async () => {
    const req = new NextRequest("http://localhost:3000/api/geolocation");
    const res = await GET(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    // Should fallback or return nulls
    expect(data.location).toBeDefined();
    expect(data.location.city).toBe("Toronto");
  });
});
