import { NextRequest, NextResponse } from "next/server";
import { LRUCache } from "lru-cache";
import { logger } from "@/utils/logger";

type RateLimitOptions = {
  uniqueTokenPerInterval?: number;
  interval?: number;
};

const tokenCache = new LRUCache<string, number>({
  max: 500, // Max 500 unique IPs per interval
  ttl: 60000, // 1 minute
  allowStale: false,
});

/**
 * Check if the request has exceeded the rate limit.
 * @param req NextRequest
 * @param limit Max requests per interval (default 60)
 * @returns NextResponse (429) if limited, null otherwise
 */
export async function checkRateLimit(req: NextRequest, limit: number = 60): Promise<NextResponse | null> {
  const ip = req.ip || req.headers.get("x-forwarded-for") || "127.0.0.1";
  const token = ip.toString();

  const currentUsage = (tokenCache.get(token) || 0) + 1;
  tokenCache.set(token, currentUsage);

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
