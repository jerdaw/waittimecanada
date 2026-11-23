import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HospitalList } from "@/components/HospitalList";
import type { Hospital } from "@/app/api/hospitals/route";

vi.mock("@/components/BenchmarkCard", () => ({
  BenchmarkCard: () => null,
}));

vi.mock("@/components/TemporalPatterns", () => ({
  TemporalPatterns: () => null,
}));

vi.mock("@/components/ExpandedCardDetails", () => ({
  ExpandedCardDetails: ({ hospital }: { hospital: { id: string } }) => (
    <div data-testid={`expanded-${hospital.id}`}>Expanded details</div>
  ),
}));

// Mock scrollIntoView since it's not implemented in JSDOM
// Element.prototype.scrollIntoView = vi.fn();
window.HTMLElement.prototype.scrollIntoView = vi.fn();

const mockHospitals: Hospital[] = [
  {
    id: "h1",
    name: "General Hospital",
    city: "Toronto",
    province: "ON",
    current_wait_time: 120,
    last_updated: new Date().toISOString(),
    is_verified: true,
    telehealth_number: "811",
    latitude: 43.65,
    longitude: -79.38,
  } as Hospital,
  {
    id: "h2",
    name: "City Hospital",
    city: "Toronto",
    province: "ON",
    current_wait_time: 45,
    last_updated: new Date().toISOString(),
    is_verified: true,
    latitude: 43.7,
    longitude: -79.4,
  } as Hospital,
];

describe("HospitalList", () => {
  it("renders list of hospitals", () => {
    render(
      <HospitalList
        hospitals={mockHospitals}
        selectedId={null}
        onSelect={() => {}}
      />,
    );

    expect(screen.getByText("General Hospital")).toBeDefined();
    expect(screen.getByText("City Hospital")).toBeDefined();
  });

  // Note: Search input tests removed - search functionality moved to Header component

  it("renders empty state message when no hospitals found", () => {
    render(
      <HospitalList
        hospitals={[]}
        selectedId={null}
        onSelect={() => {}}
        searchQuery="invalid"
      />,
    );

    // Compact layout now shows simpler "No hospitals found" message
    expect(screen.getByText("No hospitals found")).toBeDefined();
    expect(screen.getByText("Clear search")).toBeDefined();
  });

  it("renders distance when userLocation is provided", () => {
    const userLocation = { lat: 43.65, lon: -79.38 }; // Near h1

    render(
      <HospitalList
        hospitals={mockHospitals}
        selectedId={null}
        onSelect={() => {}}
        userLocation={userLocation}
      />,
    );

    // Should show distance badge (distance format: Xm or X.Xkm)
    expect(screen.getAllByText(/\d+(\.\d+)?(m|km)/).length).toBeGreaterThan(0);
  });

  it("expands card on click", () => {
    const onSelect = vi.fn();
    render(
      <HospitalList
        hospitals={mockHospitals}
        selectedId={null}
        onSelect={onSelect}
      />,
    );

    const card = screen.getByText("General Hospital").closest("button");
    expect(card).toBeDefined();

    fireEvent.click(card!); // Expand
    expect(onSelect).toHaveBeenCalledWith("h1");
  });

  it("does not mount expanded details for collapsed rows", () => {
    render(
      <HospitalList
        hospitals={mockHospitals}
        selectedId={null}
        onSelect={() => {}}
      />,
    );

    expect(screen.queryByTestId("expanded-h1")).not.toBeInTheDocument();
    expect(screen.queryByTestId("expanded-h2")).not.toBeInTheDocument();

    const button1 = screen.getByText("General Hospital").closest("button");
    fireEvent.click(button1!);

    expect(screen.getByTestId("expanded-h1")).toBeInTheDocument();
    expect(screen.queryByTestId("expanded-h2")).not.toBeInTheDocument();
  });

  it("toggles expansion state independently", () => {
    render(
      <HospitalList
        hospitals={mockHospitals}
        selectedId={null}
        onSelect={() => {}}
      />,
    );

    const button1 = screen.getByText("General Hospital").closest("button");
    fireEvent.click(button1!);

    // Check if container has visual state indicating expansion
    const card1 = button1!.closest("div"); // The outer container
    expect(card1).toBeDefined();
    // We check for shadow-lg class which indicates expanded state
    expect(card1?.className).toContain("shadow-lg");

    // Click again to collapse
    fireEvent.click(button1!);
    expect(card1?.className).not.toContain("shadow-lg");
  });

  it("toggles live data filter callback", () => {
    const onToggleLiveOnly = vi.fn();

    render(
      <HospitalList
        hospitals={mockHospitals}
        selectedId={null}
        onSelect={() => {}}
        showLiveOnly={false}
        onToggleLiveOnly={onToggleLiveOnly}
      />,
    );

    // Toggle filter
    const filterBtn = screen.getByText("Live Only");
    fireEvent.click(filterBtn);

    expect(onToggleLiveOnly).toHaveBeenCalledWith(true);
  });

  it("displays correct count when filtered", () => {
    // Pass filtered list (simulating parent filter)
    render(
      <HospitalList
        hospitals={[mockHospitals[0]]}
        selectedId={null}
        onSelect={() => {}}
        showLiveOnly={true}
        onToggleLiveOnly={() => {}}
      />,
    );

    // Check count message (now shows "X results" format)
    expect(screen.getByText(/1 results/)).toBeInTheDocument();
  });

  it("renders region selector and forwards region change", () => {
    const onRegionChange = vi.fn();

    render(
      <HospitalList
        hospitals={mockHospitals}
        selectedId={null}
        onSelect={() => {}}
        regionOptions={[
          {
            region_id: "ca-on-region-east",
            region_name: "East Health Region",
            hospital_count: 2,
            reporting_count: 2,
          },
        ]}
        selectedRegionId={null}
        onRegionChange={onRegionChange}
      />,
    );

    const combobox = screen.getByRole("combobox");
    fireEvent.change(combobox, { target: { value: "ca-on-region-east" } });

    expect(onRegionChange).toHaveBeenCalledWith("ca-on-region-east");
  });

  describe("wait-time freshness", () => {
    const base = {
      city: "Vancouver",
      province: "BC",
      is_verified: true,
      latitude: 49.2,
      longitude: -123.1,
      source_id: "bc-phsa",
    };

    it("shows the LIVE badge and value only for a current value", () => {
      render(
        <HospitalList
          hospitals={[
            {
              ...base,
              id: "c",
              name: "Current Hospital",
              current_wait_time: 55,
              wait_time_status: "current",
              last_updated: new Date().toISOString(),
            } as Hospital,
          ]}
          selectedId={null}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.getByText("LIVE")).toBeInTheDocument();
      expect(screen.getByText("55")).toBeInTheDocument();
    });

    it("shows No current data and the last report date for a stale value", () => {
      render(
        <HospitalList
          hospitals={[
            {
              ...base,
              id: "s",
              name: "Delta Hospital",
              wait_time_status: "stale",
              last_updated: "2026-06-04T23:33:00.000Z",
            } as Hospital,
          ]}
          selectedId={null}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.getByText("No current data")).toBeInTheDocument();
      expect(screen.getByText(/Last reported .*2026/)).toBeInTheDocument();
      expect(screen.queryByText("LIVE")).not.toBeInTheDocument();
      expect(screen.queryByText("380")).not.toBeInTheDocument();
      expect(screen.queryByText("--")).not.toBeInTheDocument();
    });

    it("labels an Ontario value as a monthly average and never LIVE", () => {
      render(
        <HospitalList
          hospitals={[
            {
              ...base,
              id: "o",
              name: "Ontario Hospital",
              province: "ON",
              source_id: "ontario-health",
              monthly_average_minutes: 30,
              wait_time_status: "monthly",
              // The collector ran a minute ago; that must not make it LIVE.
              last_updated: new Date().toISOString(),
            } as Hospital,
          ]}
          selectedId={null}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.queryByText("LIVE")).not.toBeInTheDocument();
      expect(screen.getByText("Monthly average")).toBeInTheDocument();
      expect(screen.getByText("30")).toBeInTheDocument();
      expect(screen.getByText(/Last checked/)).toBeInTheDocument();
    });

    it("does not show LIVE when the status is missing", () => {
      render(
        <HospitalList
          hospitals={[
            {
              ...base,
              id: "m",
              name: "No Status Hospital",
              current_wait_time: 99,
              last_updated: new Date().toISOString(),
            } as Hospital,
          ]}
          selectedId={null}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.queryByText("LIVE")).not.toBeInTheDocument();
    });
  });
});
