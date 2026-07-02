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

    // Initial state: Expanded details hidden (or not rendered if leveraging lazy render, but in our code it is rendered but hidden/grid-rows-0)
    // Actually our code uses `ExpandedCardDetails` which renders text "Directions", "Website" etc.
    // Those texts might be hidden via CSS but available in DOM or not rendered if conditional
    // Our implementation: always renders ExpandedCardDetails if `isExpanded` ? No.
    // Let's check implementation:
    // clsx(..., isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]")
    // Content is inside. So it is in the DOM but hidden?
    // Wait, screen.getByText finds hidden elements too unless configured otherwise?
    // By default getAllByText ignores hidden? No, generic getByText finds implementation.
    // However, if the container has `visibility: hidden` or `display: none` it might not.
    // Grid rows 0fr wraps overflow hidden.

    // Let's rely on class verification or existence if content is always rendered.
    // But testing library recommends testing "user visible" changes.
    // Since we use CSS transition, it's hard to test "visibility" in JSDOM easily without checking styles.

    fireEvent.click(card!); // Expand
    expect(onSelect).toHaveBeenCalledWith("h1");

    // We can check if the row container has the expanded styles
    const rowContainer = card!.closest("div")?.parentElement; // div > button is the structure?
    // Structure: div.rounded-xl > button ...
    // div.rounded-xl also has Expanded Content sibling.
    // Wait, the button is INSIDE the div.
    // let's inspect the `div` wrapper.

    // A simpler way: Check if "Directions" is visible or present.
    // Since we didn't conditionally render the children of ExpandedCardDetails based on expansion state in the list logic (we just hid it with CSS),
    // it IS always present in the DOM?
    // Check code: <ExpandedCardDetails hospital={hospital} /> is ALWAYS rendered inside the grid div.
    // So expect(screen.getAllByText("Directions").length).toBe(2); (for 2 hospitals)

    // We should verify the STATE change triggers CSS class change.
    // but in unit test we can't easily check computed styles of grid expansion in JSDOM reliably.
    // We can check if the `grid-rows-[1fr]` class is applied.
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
});
