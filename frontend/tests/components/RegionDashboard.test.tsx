import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RegionDashboard } from "@/components/RegionDashboard";

describe("RegionDashboard", () => {
  it("renders region cards with metrics", () => {
    render(
      <RegionDashboard
        province="ON"
        period="7d"
        provinceMean={132}
        mappingCoverage={{
          mapped_hospitals: 8,
          total_hospitals: 10,
          coverage_percent: 80,
        }}
        selectedRegionId={null}
        onSelectRegion={() => {}}
        regions={[
          {
            region_id: "ca-on-region-east",
            region_name: "East Health Region",
            region_code: "EAST",
            hospital_count: 4,
            reporting_count: 4,
            period_mean: 120,
            period_median: 118,
            best_wait: 90,
            worst_wait: 150,
            trend: "improving",
            trend_change_percent: -8.4,
            hospital_ids: ["h1", "h2"],
            percentile: 25,
            quartile: 1,
          },
        ]}
      />,
    );

    expect(screen.getByText("Regional Intelligence")).toBeInTheDocument();
    expect(screen.getByText("East Health Region")).toBeInTheDocument();
    expect(screen.getByText("Improving 8.4%")).toBeInTheDocument();
    expect(screen.getByText("120 min")).toBeInTheDocument();
    expect(screen.getByText(/Mapping coverage:/)).toBeInTheDocument();
  });

  it("calls onSelectRegion for card and clear button", () => {
    const onSelectRegion = vi.fn();

    render(
      <RegionDashboard
        province="ON"
        period="7d"
        provinceMean={null}
        selectedRegionId={null}
        onSelectRegion={onSelectRegion}
        regions={[
          {
            region_id: "ca-on-region-east",
            region_name: "East Health Region",
            region_code: "EAST",
            hospital_count: 4,
            reporting_count: 2,
            period_mean: 120,
            period_median: 118,
            best_wait: 90,
            worst_wait: 160,
            trend: "stable",
            trend_change_percent: 0,
            hospital_ids: ["h1"],
            percentile: 50,
            quartile: 2,
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByText("East Health Region"));
    expect(onSelectRegion).toHaveBeenCalledWith("ca-on-region-east");

    fireEvent.click(screen.getByText("Clear Region Filter"));
    expect(onSelectRegion).toHaveBeenCalledWith(null);
  });

  it("renders loading state", () => {
    render(
      <RegionDashboard
        province="ON"
        period="7d"
        provinceMean={null}
        selectedRegionId={null}
        onSelectRegion={() => {}}
        regions={[]}
        loading
      />,
    );

    expect(
      screen.getByText("Loading regional analytics..."),
    ).toBeInTheDocument();
  });
});
