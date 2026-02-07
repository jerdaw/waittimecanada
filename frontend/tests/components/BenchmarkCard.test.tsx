import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { BenchmarkCard } from "@/components/BenchmarkCard";
import type { Hospital } from "@/app/api/hospitals/route";

const mockHospital: Hospital = {
  id: "ca-on-test-hospital",
  name: "Test Hospital",
  province: "ON",
  city: "Ottawa",
  latitude: 45.42,
  longitude: -75.69,
  is_verified: true,
  is_visible: true,
  source_id: "ontario-health",
};

describe("BenchmarkCard", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders percentile badge and province context", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          province: "ON",
          period: "7d",
          generated_at: "2026-02-07T00:00:00.000Z",
          hospital_count: 3,
          province_stats: {
            mean: 120,
            median: 120,
            p25: 100,
            p75: 140,
            min: 90,
            max: 150,
          },
          hospitals: [
            {
              hospital_id: "ca-on-test-hospital",
              hospital_name: "Test Hospital",
              city: "Ottawa",
              current_wait: 130,
              period_mean: 130,
              percentile: 67,
              quartile: 3,
              trend: "worsening",
              trend_change_percent: 8.5,
            },
          ],
        },
      }),
    } as Response);

    render(<BenchmarkCard hospital={mockHospital} />);

    await waitFor(() => {
      expect(screen.getByText(/67th percentile wait time/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Q3 - Above Typical/i)).toBeInTheDocument();
    expect(screen.getByText(/Ontario avg: 120 min/i)).toBeInTheDocument();
  });

  it("renders compact variant", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          province: "ON",
          period: "7d",
          generated_at: "2026-02-07T00:00:00.000Z",
          hospital_count: 2,
          province_stats: {
            mean: 110,
            median: 110,
            p25: 100,
            p75: 120,
            min: 95,
            max: 130,
          },
          hospitals: [
            {
              hospital_id: "ca-on-test-hospital",
              hospital_name: "Test Hospital",
              city: "Ottawa",
              current_wait: 95,
              period_mean: 95,
              percentile: 50,
              quartile: 2,
              trend: "improving",
              trend_change_percent: -7.1,
            },
          ],
        },
      }),
    } as Response);

    render(<BenchmarkCard hospital={mockHospital} compact />);

    await waitFor(() => {
      expect(screen.getByText(/Peer Rank/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/50th percentile/i)).toBeInTheDocument();
    expect(screen.getByText(/Province avg: 110 min/i)).toBeInTheDocument();
  });

  it("renders nothing when benchmark data is unavailable", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      json: async () => ({ success: false }),
    } as Response);

    const { container } = render(<BenchmarkCard hospital={mockHospital} />);

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });
});
