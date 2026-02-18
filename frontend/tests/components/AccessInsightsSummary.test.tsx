import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AccessInsightsSummary } from "@/components/insights/AccessInsightsSummary";
import type { Hospital } from "@/app/api/hospitals/route";

describe("AccessInsightsSummary", () => {
  const hospitals: Hospital[] = [
    {
      id: "h1",
      name: "Test Hospital",
      province: "ON",
      city: "Toronto",
      latitude: 43.65,
      longitude: -79.38,
      is_verified: true,
      is_visible: true,
      source_id: "src-on",
      current_wait_time: 110,
      last_updated: "2026-02-08T00:00:00.000Z",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("shows equity not-available state", async () => {
    // @ts-ignore
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: {
            province: "ON",
            period: "7d",
            status: "not_available_yet",
            generated_at: "2026-02-08T00:00:00.000Z",
            is_placeholder: false,
            message: "Equity linkage summary not available yet.",
            setup_steps: ["Integrate provincial census tract income dataset"],
          },
        }),
    });

    render(
      <AccessInsightsSummary
        hospitals={hospitals}
        userLocation={null}
        province="ON"
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Equity linkage summary not available yet"),
      ).toBeInTheDocument();
    });
  });

  it("renders linkage metrics when equity summary is ready", async () => {
    // @ts-ignore
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: {
            province: "ON",
            period: "7d",
            status: "ready",
            generated_at: "2026-02-08T00:00:00.000Z",
            is_placeholder: false,
            message: "Computed from Ontario tract data",
            low_income_tracts: 3,
            total_tracts: 5,
            reporting_hospitals: 12,
            hospitals_near_low_income: 7,
            province_avg_wait: 120,
            near_low_income_avg_wait: 135,
            wait_gap_minutes: 15,
            threshold_km: 30,
            methodology: {
              interpretation: "descriptive_association_only",
              causal_inference: false,
              census_income_reference_year: 2021,
              wait_aggregation_period: "7d",
            },
          },
        }),
    });

    render(
      <AccessInsightsSummary
        hospitals={hospitals}
        userLocation={{ lat: 43.66, lon: -79.4 }}
        province="ON"
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Equity Access Snapshot (7d)"),
      ).toBeInTheDocument();
      expect(screen.getByText("Low-Income Tracts")).toBeInTheDocument();
      expect(screen.getByText("Hospitals Near Tracts")).toBeInTheDocument();
      expect(screen.getByText("Wait Gap vs Province")).toBeInTheDocument();
      expect(screen.getByText("Interpretation limits")).toBeInTheDocument();
      expect(
        screen.getByText(/does not establish causality/i),
      ).toBeInTheDocument();
      expect(
        screen.queryByText(/Placeholder tract dataset in use/i),
      ).not.toBeInTheDocument();
    });
  });
});
