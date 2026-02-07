/**
 * Tests for Map component with prop-based data
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Map from "@/components/Map";
import { Hospital } from "@/app/api/hospitals/route";

// Mock MapboxGL
vi.mock("react-map-gl", () => ({
  default: ({ children, onClick }: { children: React.ReactNode, onClick: () => void }) => (
    <div data-testid="mapbox-map" onClick={onClick}>{children}</div>
  ),
  Marker: ({ children, onClick }: { children: React.ReactNode, onClick: (e: any) => void }) => (
    <div data-testid="map-marker" onClick={(e) => onClick({ originalEvent: { stopPropagation: () => {} } })}>{children}</div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-popup">{children}</div>
  ),
  NavigationControl: () => <div data-testid="navigation-control" />,
}));

// Mock Mapbox CSS
vi.mock("mapbox-gl/dist/mapbox-gl.css", () => ({}));

// Mock environment variable
vi.stubEnv("NEXT_PUBLIC_MAPBOX_TOKEN", "pk.test_token");

// Mock TrendChart to avoid complex rendering in Map tests
vi.mock("@/components/TrendChart", () => ({
  TrendChart: () => <div data-testid="trend-chart">Trend Chart Mock</div>,
}));

vi.mock("@/components/BenchmarkCard", () => ({
  BenchmarkCard: () => <div data-testid="benchmark-card">Benchmark Card Mock</div>,
}));

describe("Map Component", () => {
  const mockHospitals: Hospital[] = [
    {
      id: "test-hospital",
      name: "Test Hospital",
      province: "ON",
      city: "TestCity",
      latitude: 45.0,
      longitude: -75.0,
      is_verified: true,
      is_visible: true,
      source_id: "test-source",
      current_wait_time: 90,
      last_updated: new Date().toISOString(),
      metric_family: "TIME_TO_PROVIDER",
      start_event: "TRIAGE",
      end_event: "PHYSICIAN",
      statistic_type: "P90",
      patient_scope: "ALL",
    },
  ];

  const defaultProps = {
    hospitals: [],
    selectedId: null,
    onSelect: vi.fn(),
    lastUpdate: null,
    isStale: false,
    loading: false,
    error: null,
  };

  it("renders loading state", () => {
    render(<Map {...defaultProps} loading={true} />);
    expect(screen.getByText("Loading hospitals...")).toBeInTheDocument();
  });

  it("renders error state", () => {
    render(<Map {...defaultProps} error="Failed to load" />);
    expect(screen.getByText("Unable to load map")).toBeInTheDocument();
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
  });

  it("renders map with markers when data is provided", () => {
    render(<Map {...defaultProps} hospitals={mockHospitals} />);
    expect(screen.getByTestId("mapbox-map")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // Count badge
    expect(screen.getByTestId("map-marker")).toBeInTheDocument();
  });

  it("calls onSelect when marker is clicked", () => {
    const onSelect = vi.fn();
    render(<Map {...defaultProps} hospitals={mockHospitals} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByTestId("map-marker"));
    expect(onSelect).toHaveBeenCalledWith("test-hospital");
  });

  it("calls onSelect(null) when map background is clicked", () => {
    const onSelect = vi.fn();
    render(<Map {...defaultProps} hospitals={mockHospitals} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByTestId("mapbox-map"));
    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("shows popup when hospital is selected", () => {
    render(<Map {...defaultProps} hospitals={mockHospitals} selectedId="test-hospital" />);
    expect(screen.getByTestId("map-popup")).toBeInTheDocument();
    expect(screen.getByText("Test Hospital")).toBeInTheDocument();
  });

  it("displays freshness indicator", () => {
    render(<Map {...defaultProps} lastUpdate="2023-01-01" isStale={true} />);
    expect(screen.getByText("Data may be stale")).toBeInTheDocument();
  });

  it("displays quick action buttons in popup", () => {
    // @ts-ignore
    const hospitalWithInfo = {
      ...mockHospitals[0],
      telehealth_number: "123-456-7890",
    };
    render(<Map {...defaultProps} hospitals={[hospitalWithInfo]} selectedId="test-hospital" />);
    
    expect(screen.getByText("Directions")).toBeInTheDocument();
    // Website button removed
    expect(screen.getByText("Call Health Info")).toBeInTheDocument();
  });
});
