import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AnalyticsPage from "@/app/[locale]/analytics/page";

vi.mock("@/components/Header", () => ({
  Header: () => <header data-testid="mock-header">Header</header>,
}));

vi.mock("@/components/SystemTrendChart", () => ({
  SystemTrendChart: () => (
    <section data-testid="mock-system-trend">System Trend Chart</section>
  ),
}));

vi.mock("@/components/RegionDashboard", () => ({
  RegionDashboard: ({ loading }: { loading?: boolean }) => (
    <section data-testid="mock-region-dashboard">
      {loading ? "Region loading" : "Region ready"}
    </section>
  ),
}));

describe("AnalyticsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("renders all analytics sections and ranking rows", async () => {
    // @ts-ignore
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            data: {
              regions: [
                {
                  region_id: "ca-on-region-east",
                  region_name: "East Health Region",
                  region_code: "EAST",
                  hospital_count: 1,
                  reporting_count: 1,
                  period_mean: 120,
                  period_median: 120,
                  best_wait: 110,
                  worst_wait: 130,
                  trend: "stable",
                  trend_change_percent: 0,
                  hospital_ids: ["h1"],
                  percentile: 50,
                  quartile: 2,
                },
              ],
              province_mean: 120,
            },
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            data: {
              hospitals: [
                {
                  hospital_id: "h1",
                  hospital_name: "Test Hospital",
                  city: "Ottawa",
                  current_wait: 125,
                  period_mean: 125,
                  percentile: 70,
                  quartile: 3,
                  trend: "worsening",
                  trend_change_percent: 8.2,
                },
              ],
            },
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            data: {
              province: "ON",
              available: false,
              status: "not_available_yet",
              generated_at: "2026-02-08T00:00:00.000Z",
              message:
                "Occupancy metrics are not available from the current provincial feed.",
              fields: {
                patients_waiting: false,
                patients_in_treatment: false,
              },
              setup_steps: [
                "Verify provincial source publishes occupancy fields",
              ],
            },
          }),
      });

    render(<AnalyticsPage />);

    expect(screen.getByTestId("mock-header")).toBeInTheDocument();
    expect(screen.getByText("Analytics Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Regional Overview")).toBeInTheDocument();
    expect(screen.getByText("Occupancy Signals")).toBeInTheDocument();
    expect(screen.getByText("Hospital Rankings")).toBeInTheDocument();
    expect(screen.getByTestId("mock-system-trend")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Test Hospital")).toBeInTheDocument();
    });
    expect(
      screen.getByText("Occupancy metrics not available yet"),
    ).toBeInTheDocument();
  });

  it("shows loading state for ranking table", () => {
    // @ts-ignore
    global.fetch.mockImplementation(() => new Promise(() => {}));

    render(<AnalyticsPage />);

    expect(
      screen.getByText("Loading benchmark rankings..."),
    ).toBeInTheDocument();
  });

  it("shows setup guidance when regional schema is not initialized", async () => {
    // @ts-ignore
    global.fetch
      .mockResolvedValueOnce({
        ok: false,
        json: () =>
          Promise.resolve({
            success: false,
            setup_required: true,
            message: "Missing regions tables",
            setup_steps: ["python backend/run_migrations.py"],
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            data: {
              hospitals: [],
            },
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            data: {
              province: "ON",
              available: false,
              status: "not_available_yet",
              generated_at: "2026-02-08T00:00:00.000Z",
              message:
                "Occupancy metrics are not available from current sources.",
              fields: {
                patients_waiting: false,
                patients_in_treatment: false,
              },
              setup_steps: [],
            },
          }),
      });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Regional analytics setup needed"),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("Missing regions tables")).toBeInTheDocument();
    expect(
      screen.getByText("python backend/run_migrations.py"),
    ).toBeInTheDocument();
  });
});
