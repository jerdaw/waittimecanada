import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "../../app/api/geolocation/route";

const originalFetch = global.fetch;

function mockSuccessfulLookup() {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          latitude: 43.6532,
          longitude: -79.3832,
          city: "Toronto",
          region: "Ontario",
          country_name: "Canada",
        }),
    } as Response),
  );
}

describe("Geolocation API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSuccessfulLookup();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test("uses the first x-forwarded-for address for server-side lookup", async () => {
    const req = new NextRequest("http://localhost:3000/api/geolocation", {
      headers: {
        "x-forwarded-for": "8.8.8.8, 1.1.1.1",
        "x-real-ip": "9.9.9.9",
      },
    });

    const res = await GET(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(global.fetch).toHaveBeenCalledWith(
      "https://ipapi.co/8.8.8.8/json/",
      { headers: { "User-Agent": "WaitTimeCanada/1.0" } },
    );
    expect(data).toEqual({
      success: true,
      location: {
        lat: 43.6532,
        lon: -79.3832,
        city: "Toronto",
        region: "Ontario",
        country: "Canada",
      },
    });
  });

  test("uses x-real-ip when x-forwarded-for is missing", async () => {
    const req = new NextRequest("http://localhost:3000/api/geolocation", {
      headers: {
        "x-real-ip": "9.9.9.9",
      },
    });

    const res = await GET(req);

    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(global.fetch).toHaveBeenCalledWith(
      "https://ipapi.co/9.9.9.9/json/",
      { headers: { "User-Agent": "WaitTimeCanada/1.0" } },
    );
  });

  test("uses requester lookup for missing or loopback client IPs", async () => {
    const req = new NextRequest("http://localhost:3000/api/geolocation", {
      headers: {
        "x-forwarded-for": "127.0.0.1",
      },
    });

    const res = await GET(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(global.fetch).toHaveBeenCalledWith("https://ipapi.co/json/", {
      headers: { "User-Agent": "WaitTimeCanada/1.0" },
    });
    expect(data.location.city).toBe("Toronto");
  });

  test("returns no-store Toronto fallback when upstream lookup fails", async () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 503,
      } as Response),
    );
    const req = new NextRequest("http://localhost:3000/api/geolocation");

    const res = await GET(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
    expect(data).toEqual({
      success: true,
      location: {
        lat: 43.6532,
        lon: -79.3832,
        city: "Toronto",
        region: "Ontario",
        country: "Canada",
      },
      fallback: true,
    });

    errorSpy.mockRestore();
  });
});
