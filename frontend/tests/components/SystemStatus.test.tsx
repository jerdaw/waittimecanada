import { render, screen, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { SystemStatus } from "@/components/SystemStatus";

describe("SystemStatus", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
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

  it("displays degraded status when data is stale (60-120 min)", async () => {
    const staleTime = new Date(Date.now() - 90 * 60 * 1000); // 90 minutes ago
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: true,
        last_update: staleTime.toISOString(),
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

    expect(screen.getByText(/updated 90m ago/i)).toBeInTheDocument();
  });

  it("displays down status when data is very stale (>120 min)", async () => {
    const veryStaleTime = new Date(Date.now() - 180 * 60 * 1000); // 3 hours ago
    (global.fetch as any).mockResolvedValue({
      json: async () => ({
        healthy: false,
        last_update: veryStaleTime.toISOString(),
        sources: [{ source_id: "test", status: "error" }],
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

  it("displays down status when API returns unhealthy", async () => {
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
});
