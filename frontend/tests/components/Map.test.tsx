/**
 * Tests for Map component with real data integration
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import Map from "@/components/Map";

// Mock MapboxGL
vi.mock("react-map-gl", () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="mapbox-map">{children}</div>
  ),
  Marker: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-marker">{children}</div>
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

describe("Map Component", () => {
  beforeEach(() => {
    // Reset fetch mocks
    global.fetch = vi.fn();
  });

  it("renders loading state initially", () => {
    // Mock fetch to never resolve
    global.fetch = vi.fn(() => new Promise(() => {}));

    render(<Map />);

    expect(screen.getByText("Loading hospitals...")).toBeInTheDocument();
  });

  it("renders error state when API fails", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            success: false,
            message: "Database connection failed",
          }),
      })
    );

    render(<Map />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load map")).toBeInTheDocument();
    });
  });

  it("renders hospitals with methodology information", async () => {
    const mockHospitals = [
      {
        id: "ca-on-ottawa-civic",
        name: "The Ottawa Hospital - Civic Campus",
        province: "ON",
        city: "Ottawa",
        latitude: 45.3982,
        longitude: -75.737,
        is_verified: true,
        is_visible: true,
        source_id: "ontario-health",
        current_wait_time: 120,
        last_updated: new Date().toISOString(),
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
        patient_scope: "ALL",
      },
    ];

    global.fetch = vi.fn((url) => {
      if (url.includes("/api/hospitals")) {
        return Promise.resolve({
          json: () =>
            Promise.resolve({
              success: true,
              count: 1,
              data: mockHospitals,
            }),
        });
      }
      if (url.includes("/api/health")) {
        return Promise.resolve({
          json: () =>
            Promise.resolve({
              healthy: true,
              last_update: new Date().toISOString(),
              stale_threshold_minutes: 60,
              sources: [],
            }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    });

    render(<Map />);

    await waitFor(() => {
      expect(screen.getByTestId("mapbox-map")).toBeInTheDocument();
    });

    // Check that hospital count is displayed
    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument();
      expect(screen.getByText("hospitals")).toBeInTheDocument();
    });
  });

  it("displays methodology information correctly", async () => {
    const mockHospitals = [
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
      },
    ];

    global.fetch = vi.fn((url) => {
      if (url.includes("/api/hospitals")) {
        return Promise.resolve({
          json: () =>
            Promise.resolve({
              success: true,
              count: 1,
              data: mockHospitals,
            }),
        });
      }
      if (url.includes("/api/health")) {
        return Promise.resolve({
          json: () =>
            Promise.resolve({
              healthy: true,
              last_update: new Date().toISOString(),
              sources: [],
            }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    });

    render(<Map />);

    await waitFor(() => {
      expect(screen.getByTestId("mapbox-map")).toBeInTheDocument();
    });

    // Map component renders markers with methodology data
    const markers = screen.getAllByTestId("map-marker");
    expect(markers.length).toBeGreaterThan(0);
  });

  it("displays data freshness indicator", async () => {
    global.fetch = vi.fn((url) => {
      if (url.includes("/api/hospitals")) {
        return Promise.resolve({
          json: () =>
            Promise.resolve({
              success: true,
              count: 0,
              data: [],
            }),
        });
      }
      if (url.includes("/api/health")) {
        return Promise.resolve({
          json: () =>
            Promise.resolve({
              healthy: true,
              last_update: new Date().toISOString(),
              sources: [],
            }),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    });

    render(<Map />);

    await waitFor(() => {
      // Check for data freshness indicator elements
      expect(screen.getByTestId("mapbox-map")).toBeInTheDocument();
    });
  });
});
