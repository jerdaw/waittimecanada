import { beforeEach, describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { checkRateLimit, resetRateLimitForTests } from "./rate-limit";

function requestWithHeaders(headers: Record<string, string>) {
  return new NextRequest("http://localhost/api/test", { headers });
}

describe("API Rate Limiting Integration", () => {
  beforeEach(() => {
    resetRateLimitForTests();
  });

  it("uses the first x-forwarded-for IP ahead of other proxy headers", async () => {
    const first = requestWithHeaders({
      "x-forwarded-for": "203.0.113.10, 203.0.113.11",
      "x-real-ip": "203.0.113.20",
    });
    const second = requestWithHeaders({
      "x-forwarded-for": "203.0.113.10, 203.0.113.12",
      "x-real-ip": "203.0.113.21",
    });

    expect(await checkRateLimit(first, 1)).toBeNull();

    const blocked = await checkRateLimit(second, 1);

    expect(blocked?.status).toBe(429);
    expect(blocked?.headers.get("X-RateLimit-Limit")).toBe("1");
    expect(blocked?.headers.get("X-RateLimit-Remaining")).toBe("0");
    expect(await blocked?.json()).toEqual({ error: "Too Many Requests" });
  });

  it("falls back to x-real-ip when x-forwarded-for is absent", async () => {
    const first = requestWithHeaders({
      "x-real-ip": "203.0.113.30",
      "cf-connecting-ip": "203.0.113.31",
    });
    const second = requestWithHeaders({
      "x-real-ip": "203.0.113.30",
      "cf-connecting-ip": "203.0.113.32",
    });

    expect(await checkRateLimit(first, 1)).toBeNull();

    const blocked = await checkRateLimit(second, 1);

    expect(blocked?.status).toBe(429);
  });

  it("falls back to cf-connecting-ip when earlier proxy headers are absent", async () => {
    const first = requestWithHeaders({
      "cf-connecting-ip": "203.0.113.40",
    });
    const second = requestWithHeaders({
      "cf-connecting-ip": "203.0.113.40",
    });

    expect(await checkRateLimit(first, 1)).toBeNull();

    const blocked = await checkRateLimit(second, 1);

    expect(blocked?.status).toBe(429);
    expect(blocked?.headers.get("Retry-After")).toBe("60");
  });
});
