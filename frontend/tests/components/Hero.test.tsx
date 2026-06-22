import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Hero } from "../../components/Hero";
import { Hospital } from "@/app/api/hospitals/route";

describe("Hero Component", () => {
  const mockHospitals: Hospital[] = [
    {
      id: "h1",
      name: "Long Wait Hospital",
      city: "City A",
      province: "ON",
      current_wait_time: 120,
      latitude: 0,
      longitude: 0,
      is_visible: true,
      is_verified: true,
      source_id: "ontario-health",
      last_updated: new Date().toISOString(),
    },
    {
      id: "h2",
      name: "Short Wait Hospital",
      city: "City B",
      province: "ON",
      current_wait_time: 30, // Shortest
      latitude: 0,
      longitude: 0,
      is_visible: true,
      is_verified: true,
      source_id: "ontario-health",
      last_updated: new Date().toISOString(),
    },
    {
      id: "h3",
      name: "Null Wait Hospital",
      city: "City C",
      province: "ON",
      current_wait_time: undefined,
      latitude: 0,
      longitude: 0,
      is_visible: true,
      is_verified: true,
      source_id: "ontario-health",
      last_updated: new Date().toISOString(),
    },
  ];

  it("renders correctly", () => {
    render(<Hero hospitals={mockHospitals} onExplore={() => {}} />);
    expect(
      screen.getByRole("heading", {
        name: /Canada.*ER.*Wait Time.*Observatory/i,
      }),
    ).toBeInTheDocument();
  });

  it("calculates and displays the shortest wait time", () => {
    render(<Hero hospitals={mockHospitals} onExplore={() => {}} />);

    // Should show Short Wait Hospital
    expect(screen.getByText("Short Wait Hospital")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();

    // Should not show Long Wait Hospital details in the shortest card
    expect(screen.queryByText("Long Wait Hospital")).not.toBeInTheDocument();
  });

  it("calls onExplore when button clicked", () => {
    const onExplore = vi.fn();
    render(<Hero hospitals={mockHospitals} onExplore={onExplore} />);

    fireEvent.click(screen.getByText("Explore Hospitals"));
    expect(onExplore).toHaveBeenCalled();
  });

  it("handles empty data gracefully", () => {
    render(<Hero hospitals={[]} onExplore={() => {}} />);
    expect(screen.getByText("Loading hospital data...")).toBeInTheDocument();
  });
});
