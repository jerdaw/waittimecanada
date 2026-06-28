import { NextRequest, NextResponse } from "next/server";
import { LRUCache } from "lru-cache";
import { logger } from "@/utils/logger";

type RateLimitOptions = {
  uniqueTokenPerInterval?: number;
  interval?: number;
};

type RateLimitEntry = {
  usage: number;
  resetAtMs: number;
};

const RATE_LIMIT_WINDOW_MS = 60000;

const tokenCache = new LRUCache<string, RateLimitEntry>({
  max: 500, // Max 500 unique IPs per interval
  ttl: RATE_LIMIT_WINDOW_MS, // 1 minute
  allowStale: false,
});

function getClientIp(req: NextRequest): string {
  const forwardedFor = req.headers
    .get("x-forwarded-for")
    ?.split(",")[0]
    ?.trim();
  return (
    forwardedFor ||
    req.headers.get("x-real-ip") ||
    req.headers.get("cf-connecting-ip") ||
    "127.0.0.1"
  );
}

/**
 * Check if the request has exceeded the rate limit.
 * @param req NextRequest
 * @param limit Max requests per interval (default 60)
 * @returns NextResponse (429) if limited, null otherwise
 */
export async function checkRateLimit(
  req: NextRequest,
  limit: number = 60,
): Promise<NextResponse | null> {
  const ip = getClientIp(req);
  const token = ip.toString();
  const now = Date.now();
  const existing = tokenCache.get(token);
  const existingUsage =
    existing && existing.resetAtMs > now ? existing.usage : 0;

  const currentUsage = existingUsage + 1;
  tokenCache.set(token, {
    usage: currentUsage,
    resetAtMs: now + RATE_LIMIT_WINDOW_MS,
  });

  const remaining = Math.max(0, limit - currentUsage);

  if (currentUsage > limit) {
    logger.warn(`Rate limit exceeded for IP: ${ip}`);
    return NextResponse.json(
      { error: "Too Many Requests" },
      {
        status: 429,
        headers: {
          "X-RateLimit-Limit": limit.toString(),
          "X-RateLimit-Remaining": "0",
          "Retry-After": "60",
        },
      },
    );
  }

  return null;
}

export function resetRateLimitForTests() {
  tokenCache.clear();
}
