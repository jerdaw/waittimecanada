import { NextRequest, NextResponse } from "next/server";
import createMiddleware from "next-intl/middleware";

const i18nMiddleware = createMiddleware({
  // A list of all locales that are supported
  locales: ["en", "fr"],

  // Used when no locale matches
  defaultLocale: "en",
});

const PUBLIC_API_CORS_HEADERS = {
  "Access-Control-Allow-Credentials": "false",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age": "86400",
} as const;

const PUBLIC_API_CORS_METHODS = new Set(["GET", "HEAD"]);

function applyPublicApiCorsHeaders(response: NextResponse) {
  Object.entries(PUBLIC_API_CORS_HEADERS).forEach(([key, value]) => {
    response.headers.set(key, value);
  });
}

export function middleware(request: NextRequest) {
  const start = performance.now();
  const isApiRequest = request.nextUrl.pathname.startsWith("/api/");

  // Canonical host redirect (domain rebrand)
  const canonicalBaseUrl =
    process.env.NEXT_PUBLIC_BASE_URL ?? "https://wait-time.ca";
  const canonical = new URL(canonicalBaseUrl);
  const canonicalHostname = canonical.hostname.toLowerCase();
  const canonicalProtocol = canonical.protocol;

  const host = (request.headers.get("host") ?? "").toLowerCase();
  const legacyHosts = new Set([
    "waittimecanada.ca",
    "www.waittimecanada.ca",
    "waittime.ca",
    "www.waittime.ca",
  ]);

  if (host && legacyHosts.has(host) && host !== canonicalHostname) {
    const url = request.nextUrl.clone();
    url.protocol = canonicalProtocol;
    url.hostname = canonicalHostname;
    url.port = "";
    return NextResponse.redirect(url, 308);
  }

  // Handle CORS preflight requests for API routes
  if (request.method === "OPTIONS" && isApiRequest) {
    const response = new NextResponse(null, { status: 204 });
    applyPublicApiCorsHeaders(response);
    return response;
  }

  // Handle actual API requests with timing
  if (isApiRequest) {
    const response = NextResponse.next();

    // Calculate duration
    const duration = performance.now() - start;

    // Add timing header
    response.headers.set("X-Response-Time", `${duration.toFixed(2)}ms`); // X-Response-Time in ms
    response.headers.set("Server-Timing", `total;dur=${duration.toFixed(2)}`); // Standard Server-Timing header
    if (PUBLIC_API_CORS_METHODS.has(request.method)) {
      applyPublicApiCorsHeaders(response);
    }

    // Log for observability via our structured logger
    // Note: Middleware runs in Edge Runtime, so this will use consoleLogger
    import("@/utils/logger").then(({ logger }) => {
      logger.info("API Request", {
        method: request.method,
        path: request.nextUrl.pathname,
        status: response.status,
        duration_ms: duration.toFixed(2),
        user_agent: request.headers.get("user-agent") || "unknown",
      });
    });

    return response;
  }

  // Handle i18n for non-API routes
  return i18nMiddleware(request);
}

// Configure which paths the middleware runs on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * API routes are matched here so the middleware can record request timing.
     * The middleware body handles API routes before delegating page requests to
     * the i18n middleware.
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
