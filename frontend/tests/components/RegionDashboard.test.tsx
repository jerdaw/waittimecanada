import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RegionDashboard } from "@/components/RegionDashboard";

// Mock next-intl explicitly here
vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}));

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

    // Expect keys instead of values
    expect(screen.getByText("title")).toBeInTheDocument();
    expect(screen.getByText("East Health Region")).toBeInTheDocument();
    // Trend label logic:
    // getTrendLabel returns t('trend.improving', {percent: ...}) -> "trend.improving"
    expect(screen.getByText("trend.improving")).toBeInTheDocument();

    // Values are formatted numbers
    expect(screen.getByText("120 min")).toBeInTheDocument();

    // Mapping coverage: t('mappingCoverage') -> "mappingCoverage"
    expect(screen.getByText(/^mappingCoverage/)).toBeInTheDocument();
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

    // "Clear Region Filter" -> "clearFilter"
    fireEvent.click(screen.getByText("clearFilter"));
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

    // "Loading regional analytics..." -> "loading"
    expect(
      screen.getByText("loading"),
    ).toBeInTheDocument();
  });
});
