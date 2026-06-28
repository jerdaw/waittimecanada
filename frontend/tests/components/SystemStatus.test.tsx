import { render, screen, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { SystemStatus } from "@/components/SystemStatus";

function mockHealthyFetch() {
  (global.fetch as any).mockImplementation(async () => ({
    json: async () => ({
      healthy: true,
      last_update: new Date().toISOString(),
      stale_threshold_minutes: 90,
      sources: [{ source_id: "test", status: "healthy" }],
    }),
  }));
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

describe("SystemStatus", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("renders loading state initially", () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<SystemStatus />);

    expect(screen.getByText("Checking...")).toBeInTheDocument();
  });

  it("displays healthy status when data is recent", async () => {
    const recentTime = new Date(Date.now() - 10 * 60 * 1000); // 10 minutes ago
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: true,
        last_update: recentTime.toISOString(),
        stale_threshold_minutes: 90,
        sources: [{ source_id: "test", status: "healthy" }],
      }),
    });

    render(<SystemStatus />);

    await waitFor(
      () => {
        expect(screen.getByText("All Systems Operational")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    expect(screen.getByText(/updated 10m ago/i)).toBeInTheDocument();
  });

  it("displays degraded status when data is stale (> threshold)", async () => {
    const staleTime = new Date(Date.now() - 100 * 60 * 1000); // 100 minutes ago
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: true,
        last_update: staleTime.toISOString(),
        stale_threshold_minutes: 90,
        sources: [{ source_id: "test", status: "stale" }],
      }),
    });

    render(<SystemStatus />);

    await waitFor(
      () => {
        expect(screen.getByText("Data May Be Stale")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );

    expect(screen.getByText(/updated 100m ago/i)).toBeInTheDocument();
  });

  it("displays down status when data is older than twice the default stale threshold", async () => {
    const veryStaleTime = new Date(Date.now() - 181 * 60 * 1000);
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: true,
        last_update: veryStaleTime.toISOString(),
        sources: [{ source_id: "test", status: "stale" }],
      }),
    });

    render(<SystemStatus />);

    await waitFor(
      () => {
        expect(screen.getByText("Data Unavailable")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("displays down status when data is older than twice a custom stale threshold", async () => {
    const veryStaleTime = new Date(Date.now() - 91 * 60 * 1000);
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: true,
        last_update: veryStaleTime.toISOString(),
        stale_threshold_minutes: 45,
        sources: [{ source_id: "test", status: "stale" }],
      }),
    });

    render(<SystemStatus />);

    await waitFor(
      () => {
        expect(screen.getByText("Data Unavailable")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("displays down status when health check fails", async () => {
    (global.fetch as any).mockRejectedValue(new Error("Network error"));

    render(<SystemStatus />);

    await waitFor(
      () => {
        expect(screen.getByText("Data Unavailable")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("displays down status when API returns unhealthy even if data is recent", async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: false,
        last_update: new Date().toISOString(),
        sources: [],
      }),
    });

    render(<SystemStatus />);

    await waitFor(
      () => {
        expect(screen.getByText("Data Unavailable")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("has accessible icon with aria-hidden", async () => {
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: true,
        last_update: new Date().toISOString(),
        sources: [],
      }),
    });

    const { container } = render(<SystemStatus />);

    await waitFor(
      () => {
        const icon = container.querySelector('svg[aria-hidden="true"]');
        expect(icon).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("polls every five minutes only when the tab is visible and refetches on visibility return", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-27T12:00:00.000Z"));
    mockHealthyFetch();
    let visibilityState = "visible";
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => visibilityState,
    });

    render(<SystemStatus />);

    await act(async () => {
      await flushPromises();
    });
    expect(global.fetch).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(5 * 60 * 1000);
      await flushPromises();
    });
    expect(global.fetch).toHaveBeenCalledTimes(2);

    visibilityState = "hidden";
    await act(async () => {
      vi.advanceTimersByTime(5 * 60 * 1000);
      await flushPromises();
    });

    expect(global.fetch).toHaveBeenCalledTimes(2);

    visibilityState = "visible";
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
      await flushPromises();
    });
    expect(global.fetch).toHaveBeenCalledTimes(3);
  });
});
