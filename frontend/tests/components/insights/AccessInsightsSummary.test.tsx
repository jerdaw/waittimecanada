import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AccessInsightsSummary } from "@/components/insights/AccessInsightsSummary";
import type { Hospital } from "@/app/api/hospitals/route";

const mockHospitals: Hospital[] = [
  {
    id: "ca-on-ottawa-civic",
    name: "Ottawa Civic Hospital",
    province: "ON",
    city: "Ottawa",
    latitude: 45.3977,
    longitude: -75.754,
    current_wait_time: 120,
    last_updated: "2024-01-01T12:00:00Z",
    is_verified: true,
    is_visible: true,
    source_id: "ontario-hqo",
  },
  {
    id: "ca-on-ottawa-general",
    name: "Ottawa General Hospital",
    province: "ON",
    city: "Ottawa",
    latitude: 45.4111,
    longitude: -75.6802,
    current_wait_time: 90,
    last_updated: "2024-01-01T12:00:00Z",
    is_verified: true,
    is_visible: true,
    source_id: "ontario-hqo",
  },
];

describe("AccessInsightsSummary", () => {
  beforeEach(() => {
    // Mock fetch to prevent real API calls and state updates
    global.fetch = vi.fn().mockResolvedValue({
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
            setup_steps: [],
          },
        }),
    });
  });

  it("renders location prompt when userLocation is null", async () => {
    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={null}
        province="ON"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/enable location access/i)).toBeInTheDocument();
    });
  });

  it("displays statistics when userLocation is provided", async () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 }; // Downtown Ottawa

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />,
    );

    // Should show stats
    await waitFor(() => {
      expect(screen.getByText(/ERs Within 30km/i)).toBeInTheDocument();
      expect(screen.getByText(/Avg Access Cost/i)).toBeInTheDocument();
      expect(screen.getByText(/Nearest ER/i)).toBeInTheDocument();
    });
  });

  it("displays disclaimer message", async () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/Never delay care for cost/i),
      ).toBeInTheDocument();
      expect(screen.getByText(/Call 911 for emergencies/i)).toBeInTheDocument();
    });
  });

  it("calculates hospitals within 30km correctly", async () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />,
    );

    // Both mock hospitals are within 30km of downtown Ottawa
    await waitFor(() => {
      expect(screen.getByText("2")).toBeInTheDocument(); // Count
      expect(screen.getByText(/of 2 total/i)).toBeInTheDocument();
    });
  });

  it("shows cost estimates with gas prices", async () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />,
    );

    // Should show average access cost in the stat card
    await waitFor(() => {
      expect(screen.getByText(/Avg Access Cost/i)).toBeInTheDocument();
      expect(screen.getByText(/Fuel \+ Parking/i)).toBeInTheDocument();
    });
  });

  it("identifies nearest hospital", async () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={mockHospitals}
        userLocation={userLocation}
        province="ON"
      />,
    );

    // Should show distance to nearest hospital
    await waitFor(() => {
      const distanceElement = screen.getByText(/^\d+\.\d+km$/);
      expect(distanceElement).toBeInTheDocument();
    });
  });

  it("handles empty hospital list gracefully", async () => {
    const userLocation = { lat: 45.4215, lon: -75.6972 };

    render(
      <AccessInsightsSummary
        hospitals={[]}
        userLocation={userLocation}
        province="ON"
      />,
    );

    // Should render empty state without crashing
    await waitFor(() => {
      expect(screen.getByText(/No hospitals available/i)).toBeInTheDocument();
    });
  });

  it("uses correct gas price for province", async () => {
    const userLocation = { lat: 49.2827, lon: -123.1207 }; // Vancouver
    const bcHospitals: Hospital[] = [
      {
        id: "ca-bc-vgh",
        name: "Vancouver General Hospital",
        province: "BC",
        city: "Vancouver",
        latitude: 49.2628,
        longitude: -123.1225,
        current_wait_time: 150,
        last_updated: "2024-01-01T12:00:00Z",
        is_verified: true,
        is_visible: true,
        source_id: "bc-phsa",
      },
    ];

    render(
      <AccessInsightsSummary
        hospitals={bcHospitals}
        userLocation={userLocation}
        province="BC"
      />,
    );

    // BC should use $1.75/L (shown in the distribution insight)
    await waitFor(() => {
      expect(screen.getByText(/\$1\.75\/L in BC/i)).toBeInTheDocument();
    });
  });

  it("shows non-causal and temporal limits when equity summary is ready", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          data: {
            province: "ON",
            period: "7d",
            status: "ready",
            generated_at: "2026-02-18T00:00:00.000Z",
            is_placeholder: false,
            message: "Computed from Ontario tract data",
            low_income_tracts: 4,
            total_tracts: 10,
            reporting_hospitals: 2,
            hospitals_near_low_income: 2,
            province_avg_wait: 105,
            near_low_income_avg_wait: 111,
            wait_gap_minutes: 6,
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
        hospitals={mockHospitals}
        userLocation={{ lat: 45.4215, lon: -75.6972 }}
        province="ON"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Interpretation limits")).toBeInTheDocument();
      expect(
        screen.getByText(/descriptive\/associational only/i),
      ).toBeInTheDocument();
      expect(screen.getByText(/Income reference year: 2021/i)).toBeInTheDocument();
    });
  });
});
