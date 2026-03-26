import { LRUCache } from "lru-cache";

type CacheKeyPart = string | number | boolean | null | undefined;
type ServerCacheValue = object;

const serverResponseCache = new LRUCache<string, ServerCacheValue>({
  max: 256,
  allowStale: false,
  ttlAutopurge: true,
});

const inflightRequests = new Map<string, Promise<ServerCacheValue>>();

function isServerCacheEnabled() {
  return process.env.NODE_ENV !== "test";
}

export function buildServerCacheKey(
  namespace: string,
  parts: Record<string, CacheKeyPart>,
) {
  const serializedParts = Object.entries(parts)
    .filter(([, value]) => value !== undefined)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${String(value ?? "")}`);

  return [namespace, ...serializedParts].join("|");
}

export async function getOrSetServerCache<T extends ServerCacheValue>(
  key: string,
  ttlMs: number,
  loader: () => Promise<T>,
): Promise<T> {
  if (!isServerCacheEnabled() || ttlMs <= 0) {
    return loader();
  }

  const cached = serverResponseCache.get(key) as T | undefined;
  if (cached !== undefined) {
    return cached;
  }

  const inflight = inflightRequests.get(key) as Promise<T> | undefined;
  if (inflight) {
    return inflight;
  }

  const promise = loader()
    .then((value) => {
      serverResponseCache.set(key, value, { ttl: ttlMs });
      return value;
    })
    .finally(() => {
      inflightRequests.delete(key);
    });

  inflightRequests.set(key, promise as Promise<ServerCacheValue>);
  return promise;
}

export function resetServerCacheForTests() {
  serverResponseCache.clear();
  inflightRequests.clear();
}
