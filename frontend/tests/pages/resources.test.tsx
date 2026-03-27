import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ResourcesPage from "@/app/[locale]/resources/page";

vi.mock("@/components/Header", () => ({
  Header: () => <header data-testid="mock-header">Header</header>,
}));

describe("ResourcesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("gates facilities behind search or location while keeping other sections live", async () => {
    // @ts-ignore
    global.fetch.mockImplementation((input: string | URL | Request) => {
      const url = String(input);

      if (url.includes("/api/resources/alerts")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              count: 0,
              data: [],
              meta: {
                source_status: [],
              },
            }),
        });
      }

      if (url.includes("kind=aed")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              count: 1,
              data: [
                {
                  id: "aed-1",
                  kind: "aed",
                  name: "Union Station AED",
                  province: "ON",
                  city: "Toronto",
                  latitude: 43.6453,
                  longitude: -79.3806,
                  source_id: "osm-aed",
                  source_name: "OpenStreetMap AED",
                  provenance_url: "https://www.openstreetmap.org",
                  last_refreshed_at: "2026-03-27T12:00:00.000Z",
                  freshness_state: "show",
                  caveat_class: "crowdsourced_incomplete",
                  address: "65 Front St W",
                  location_description: "Transit hub",
                  crowdsourced: true,
                  completeness_status: "incomplete",
                },
              ],
              meta: {
                source_status: [
                  {
                    source_id: "osm-aed",
                    source_name: "OpenStreetMap AED",
                    provenance_url: "https://www.openstreetmap.org",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                    freshness_state: "show",
                  },
                ],
              },
            }),
        });
      }

      if (url.includes("kind=facility") && url.includes("q=Toronto")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              count: 1,
              data: [
                {
                  id: "facility-1",
                  kind: "facility",
                  name: "Toronto General Hospital",
                  province: "ON",
                  city: "Toronto",
                  latitude: 43.6532,
                  longitude: -79.3832,
                  source_id: "mohserlo",
                  source_name: "MOHSERLO",
                  provenance_url: "https://data.ontario.ca/example",
                  last_refreshed_at: "2026-03-27T12:00:00.000Z",
                  freshness_state: "show",
                  caveat_class: "reference_directory",
                  address: "200 Elizabeth St",
                  reference_status: "directory_only",
                  location_description: "Hospital",
                },
              ],
              meta: {
                source_status: [
                  {
                    source_id: "mohserlo",
                    source_name: "MOHSERLO",
                    provenance_url: "https://data.ontario.ca/example",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                    freshness_state: "show",
                  },
                ],
              },
            }),
        });
      }

      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<ResourcesPage />);

    expect(screen.getByTestId("mock-header")).toBeInTheDocument();
    expect(screen.getByText("Public Health Resources")).toBeInTheDocument();
    expect(screen.getByText("Resources")).toBeInTheDocument();
    expect(screen.getByText("Source transparency")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Search for a facility or share your location to load reference directory results.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Toronto General Hospital"),
    ).not.toBeInTheDocument();

    expect(screen.getByText("AED locations")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Union Station AED")).toBeInTheDocument();
    });
    expect(screen.getByText("Crowdsourced")).toBeInTheDocument();
    expect(screen.getByText("Incomplete coverage")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Crowdsourced AED data. Locations may be incomplete or outdated. In an emergency, call 911 immediately.",
      ),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(
        screen.getByText("No safety alerts available right now."),
      ).toBeInTheDocument();
    });
    expect(screen.getAllByText("Current").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Last refreshed:/).length).toBeGreaterThan(0);
    expect(
      screen.getByText("Share your location to request an AQHI snapshot."),
    ).toBeInTheDocument();

    fireEvent.change(
      screen.getByPlaceholderText("Search hospitals, clinics, or services"),
      {
        target: { value: "Toronto" },
      },
    );

    await waitFor(() => {
      expect(screen.getByText("Toronto General Hospital")).toBeInTheDocument();
    });
    expect(
      screen.getByText(
        "Reference directory data. This is not a live operational status feed.",
      ),
    ).toBeInTheDocument();
  });
});
