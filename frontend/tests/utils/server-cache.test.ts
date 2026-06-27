import { afterEach, describe, expect, it, vi } from "vitest";
import {
  buildServerCacheKey,
  getOrSetServerCache,
  resetServerCacheForTests,
} from "../../utils/server-cache";

describe("server-cache", () => {
  afterEach(() => {
    resetServerCacheForTests();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("builds stable cache keys", () => {
    expect(
      buildServerCacheKey("hospitals", {
        province: "ON",
        includeHidden: undefined,
        limit: 100,
      }),
    ).toBe("hospitals|limit=100|province=ON");
  });

  it("bypasses the cache while running tests", async () => {
    vi.stubEnv("NODE_ENV", "test");
    const loader = vi
      .fn<() => Promise<{ value: number }>>()
      .mockResolvedValueOnce({ value: 1 })
      .mockResolvedValueOnce({ value: 2 });

    await expect(getOrSetServerCache("key", 5_000, loader)).resolves.toEqual({
      value: 1,
    });
    await expect(getOrSetServerCache("key", 5_000, loader)).resolves.toEqual({
      value: 2,
    });

    expect(loader).toHaveBeenCalledTimes(2);
  });

  it("reuses cached values outside the test environment", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const loader = vi
      .fn<() => Promise<{ value: number }>>()
      .mockResolvedValue({ value: 1 });

    await expect(getOrSetServerCache("key", 5_000, loader)).resolves.toEqual({
      value: 1,
    });
    await expect(getOrSetServerCache("key", 5_000, loader)).resolves.toEqual({
      value: 1,
    });

    expect(loader).toHaveBeenCalledTimes(1);
  });

  it("coalesces concurrent requests for the same key", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const loader = vi.fn(async () => {
      await Promise.resolve();
      return { value: 7 };
    });

    const [first, second] = await Promise.all([
      getOrSetServerCache("key", 5_000, loader),
      getOrSetServerCache("key", 5_000, loader),
    ]);

    expect(first).toEqual({ value: 7 });
    expect(second).toEqual({ value: 7 });
    expect(loader).toHaveBeenCalledTimes(1);
  });
});
