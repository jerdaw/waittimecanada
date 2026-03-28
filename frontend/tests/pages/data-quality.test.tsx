import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DataQualityPage from "@/app/[locale]/data-quality/page";

vi.mock("@/components/Header", () => ({
  Header: () => <header data-testid="mock-header">Header</header>,
}));

vi.mock("@/components/Footer", () => ({
  Footer: () => <footer data-testid="mock-footer">Footer</footer>,
}));

vi.mock("@/components/DataQualityCard", () => ({
  DataQualityCard: ({ source }: { source: { source_name: string } }) => (
    <div>{source.source_name}</div>
  ),
}));

vi.mock("@/components/AnomalyFeed", () => ({
  AnomalyFeed: () => <div>Anomaly Feed</div>,
}));

vi.mock("@/components/QualityDriftPanel", () => ({
  QualityDriftPanel: () => <div>Quality Drift Panel</div>,
}));

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  ComposedChart: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  CartesianGrid: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  Area: () => null,
}));

describe("DataQualityPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("shows a historical quality note when trend data spans the cadence-model shift", async () => {
    // @ts-expect-error test fetch mock
    global.fetch.mockImplementation((input: string | URL | Request) => {
      const url = String(input);

      if (url.endsWith("/api/data-quality")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              overall_status: "healthy",
              system_uptime_24h: 1,
              total_measurements_24h: 100,
              total_hospitals_reporting: 10,
              sources: [
                {
                  source_id: "ontario-health",
                  source_name: "Ontario Health",
                  province: "ON",
                  last_24h_success_rate: 1,
                  last_7d_success_rate: 0.95,
                  hospitals_reporting: 10,
                  total_hospitals: 10,
                  last_heartbeat_age_minutes: 5,
                  scraper_status: "healthy",
                },
              ],
            }),
        });
      }

      if (url.includes("view=trend")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              trend: [
                {
                  snapshot_date: "2026-03-27T00:00:00Z",
                  avg_success_rate: 0.94,
                },
                {
                  snapshot_date: "2026-03-28T00:00:00Z",
                  avg_success_rate: 0.99,
                },
              ],
              historical_annotation: {
                has_cadence_model_shift: true,
                model_change_date: "2026-03-28",
                legacy_scheduler_cadence: "15-minute",
                legacy_expected_runs_per_day: 96,
                current_scheduler_cadence: "hourly",
                current_expected_runs_per_day: 24,
              },
            }),
        });
      }

      if (url.includes("view=diff")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              has_baseline: true,
              summary: "Coverage improved vs. 7 days ago.",
              deltas: {
                success_rate_delta: 0.05,
                hospitals_reporting_delta: 1,
              },
            }),
        });
      }

      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<DataQualityPage />);

    expect(screen.getByTestId("mock-header")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Historical quality note")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Snapshots before 2026-03-28 were scored/),
    ).toBeInTheDocument();
    expect(screen.getByText("Ontario Health")).toBeInTheDocument();
  });
});
