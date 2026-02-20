import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SystemTrendChart } from "@/components/SystemTrendChart";

vi.mock("recharts", () => {
  const Monitor = ({
    children,
    data,
  }: {
    children: React.ReactNode;
    data: unknown;
  }) => (
    <div data-testid="recharts-mock" data-data={JSON.stringify(data)}>
      {children}
    </div>
  );

  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div>{children}</div>
    ),
    ComposedChart: Monitor,
    CartesianGrid: () => <div />,
    XAxis: () => <div />,
    YAxis: () => <div />,
    Tooltip: () => <div />,
    Area: () => <div />,
    Line: () => <div />,
  };
});

describe("SystemTrendChart", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("renders chart and narrative from API response", async () => {
    // @ts-ignore
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: {
            province: "ON",
            period: "monthly",
            lookback: "6m",
            generated_at: "2026-02-07T00:00:00.000Z",
            data_points: [
              {
                period_start: "2025-11-01",
                period_end: "2025-11-30",
                province_mean: 110,
                province_median: 108,
                province_p90: 140,
                hospitals_reporting: 4,
                total_measurements: 1000,
                range_min: 70,
                range_max: 220,
              },
              {
                period_start: "2025-12-01",
                period_end: "2025-12-31",
                province_mean: 145,
                province_median: 143,
                province_p90: 190,
                hospitals_reporting: 4,
                total_measurements: 1100,
                range_min: 80,
                range_max: 240,
              },
            ],
            trend_summary: {
              direction: "worsening",
              change_percent: 31.8,
              start_mean: 110,
              end_mean: 145,
              narrative:
                "Ontario ER wait times have increased approximately 31.8% over the past 6 months.",
            },
          },
        }),
    });

    render(<SystemTrendChart province="ON" />);

    await waitFor(() => {
      expect(screen.getByTestId("recharts-mock")).toBeInTheDocument();
    });

    expect(screen.getByText(/Wait Time Trend/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Ontario ER wait times have increased/i),
    ).toBeInTheDocument();
  });

  it("updates query when toggles are changed", async () => {
    // @ts-ignore
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: {
            province: "ON",
            period: "monthly",
            lookback: "6m",
            generated_at: "2026-02-07T00:00:00.000Z",
            data_points: [],
            trend_summary: {
              direction: "stable",
              change_percent: 0,
              start_mean: null,
              end_mean: null,
              narrative: "Not enough data",
            },
          },
        }),
    });

    render(<SystemTrendChart province="ON" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("period=monthly&lookback=6m"),
        expect.any(Object),
      );
    });

    fireEvent.click(screen.getByText("Weekly"));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("period=weekly"),
        expect.any(Object),
      );
    });

    fireEvent.click(screen.getByText("1y"));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("lookback=1y"),
        expect.any(Object),
      );
    });
  });

  it("renders Occupancy Trend when metricFamily is STRETCHER_OCCUPANCY", async () => {
    // @ts-ignore
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: {
            province: "QC",
            period: "monthly",
            lookback: "6m",
            generated_at: "2026-02-07T00:00:00.000Z",
            data_points: [],
            trend_summary: {
              direction: "stable",
              change_percent: 0,
              start_mean: null,
              end_mean: null,
              narrative: "Not enough data",
            },
          },
        }),
    });

    render(<SystemTrendChart province="QC" metricFamily="STRETCHER_OCCUPANCY" />);

    // Wait for data to load (mock returns success)
    await waitFor(() => {
      // The ER occupancy badge label is rendered when data loads
      expect(screen.getByText(/ER occupancy/i)).toBeInTheDocument();
    });

    // Confirm heading matches occupancy variant
    expect(screen.getByText("Occupancy Trend")).toBeInTheDocument();
  });
});
