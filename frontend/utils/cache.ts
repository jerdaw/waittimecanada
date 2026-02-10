export const NO_STORE_HEADERS = {
  "Cache-Control": "no-store",
};

export function buildPublicCacheControl(
  sMaxAgeSeconds: number,
  staleWhileRevalidateSeconds = sMaxAgeSeconds * 3,
): string {
  return `public, max-age=0, s-maxage=${sMaxAgeSeconds}, stale-while-revalidate=${staleWhileRevalidateSeconds}`;
}

export function publicCacheHeaders(
  sMaxAgeSeconds: number,
  staleWhileRevalidateSeconds = sMaxAgeSeconds * 3,
) {
  return {
    "Cache-Control": buildPublicCacheControl(
      sMaxAgeSeconds,
      staleWhileRevalidateSeconds,
    ),
  };
}
