import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { checkRateLimit, resetRateLimitForTests } from "./rate-limit";
import { NextRequest } from "next/server";
import { logger } from "@/utils/logger";

vi.mock("@/utils/logger", () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
  },
}));

function requestFromIp(ip: string) {
  return new NextRequest("http://localhost", {
    headers: { "x-forwarded-for": ip },
  });
}

describe("Rate Limiting", () => {
  beforeEach(() => {
    resetRateLimitForTests();
    vi.clearAllMocks();
    vi.useFakeTimers({
      toFake: ["Date", "setTimeout", "clearTimeout", "performance"],
    });
  });

  afterEach(() => {
    resetRateLimitForTests();
    vi.useRealTimers();
  });

  it("should allow requests under the limit", async () => {
    const req = requestFromIp("203.0.113.50");

    const limit = 5;
    for (let i = 0; i < limit; i++) {
      const res = await checkRateLimit(req, limit);
      expect(res).toBeNull();
    }
  });

  it("should block requests over the limit", async () => {
    const req = requestFromIp("203.0.113.51");

    const limit = 5;
    for (let i = 0; i < limit; i++) {
      await checkRateLimit(req, limit);
    }

    const res = await checkRateLimit(req, limit);
    expect(res).not.toBeNull();
    expect(res?.status).toBe(429);

    // Check headers
    expect(res?.headers.get("X-RateLimit-Limit")).toBe("5");
    expect(res?.headers.get("X-RateLimit-Remaining")).toBe("0");
  });

  it("should reset limit after window via LRU TTL", async () => {
    const req = requestFromIp("203.0.113.52");

    await checkRateLimit(req, 1);
    const blocked = await checkRateLimit(req, 1);
    expect(blocked?.status).toBe(429);

    vi.advanceTimersByTime(61000);

    expect(await checkRateLimit(req, 1)).toBeNull();
  });

  it("does not log raw client IPs when requests are rate limited", async () => {
    const req = requestFromIp("203.0.113.53");

    await checkRateLimit(req, 1);
    await checkRateLimit(req, 1);

    expect(logger.warn).toHaveBeenCalledTimes(1);
    expect(JSON.stringify(vi.mocked(logger.warn).mock.calls)).not.toContain(
      "203.0.113.53",
    );
  });
});
