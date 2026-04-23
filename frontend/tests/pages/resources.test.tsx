import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ResourcesPage from "@/app/[locale]/resources/page";

vi.mock("@/components/Header", () => ({
  Header: () => <header data-testid="mock-header">Header</header>,
}));

function buildSourceCatalogRecord(overrides: Record<string, unknown>) {
  return {
    connector_type: "open_data_portal",
    access_route: "Ontario Data Catalogue CSV downloads",
    license_reuse_status: "approved_with_conditions",
    attribution_requirement: "Visible official provenance required.",
    update_cadence: "annual",
    recommended_usage_mode: "scheduled_ingest",
    public_methodology_note: "Reference directory data only.",
    last_verified_at: "2026-03-27T12:00:00.000Z",
    freshness_state: "show",
    ...overrides,
  };
}

describe("ResourcesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it("renders the Ontario resource catalog, EMS system context, and gated facility search", async () => {
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
                source_status: [
                  {
                    source_id: "health-canada-recalls",
                    source_name: "Health Canada Recalls",
                    provenance_url: "https://recalls-rappels.canada.ca/example",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                    freshness_state: "show",
                  },
                ],
                source_catalog: [
                  buildSourceCatalogRecord({
                    source_id: "health-canada-recalls",
                    source_name: "Health Canada Recalls",
                    provenance_url: "https://recalls-rappels.canada.ca/example",
                    domain: "safety_alert",
                    connector_type: "feed",
                    access_route: "Health Canada recalls feed",
                    recommended_usage_mode: "scheduled_ingest",
                    public_methodology_note:
                      "Official Health Canada safety alert feed.",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                  }),
                ],
              },
            }),
        });
      }

      if (url.includes("/api/resources/system-context")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                dispatch_centres: [
                  {
                    id: "dispatch-1",
                    geography_name: "Toronto CACC",
                    reporting_year: 2024,
                    average_response_time_minutes: 8.4,
                    call_volume: 10123,
                    source_id: "ontario-land-ambulance-response-times",
                    source_name: "Ontario Land Ambulance Response Times",
                    provenance_url: "https://data.ontario.ca/resource/cacc",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                    freshness_state: "show",
                    caveat_class: "official_system_context",
                  },
                ],
                paramedic_services: [
                  {
                    id: "paramedic-1",
                    geography_name: "Toronto",
                    reporting_year: 2024,
                    severity_breakdown: [
                      {
                        patient_severity: "CTAS 1",
                        response_time_plan_minutes: 8,
                        planned_response_pct: 90,
                        performance_pct: 88.5,
                      },
                    ],
                    source_id: "ontario-land-ambulance-response-times",
                    source_name: "Ontario Land Ambulance Response Times",
                    provenance_url: "https://data.ontario.ca/resource/paramedic",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                    freshness_state: "show",
                    caveat_class: "official_system_context",
                  },
                ],
              },
              meta: {
                source_status: [
                  {
                    source_id: "ontario-land-ambulance-response-times",
                    source_name: "Ontario Land Ambulance Response Times",
                    provenance_url:
                      "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                    freshness_state: "show",
                  },
                ],
                source_catalog: [
                  buildSourceCatalogRecord({
                    source_id: "ontario-land-ambulance-response-times",
                    source_name: "Ontario Land Ambulance Response Times",
                    provenance_url:
                      "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
                    domain: "system_context",
                    recommended_usage_mode: "analytics_only",
                    public_methodology_note:
                      "Official Ontario ambulance response-time reporting for context only.",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                  }),
                ],
              },
          }),
        });
      }

      if (url.includes("/api/resources/water-advisories")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              count: 1,
              data: [
                {
                  id: "water-1",
                  community_name: "Neskantaga First Nation",
                  water_system_name: "Neskantaga Public Water System",
                  advisory_type: "Boil water advisory",
                  advisory_set_at: "1995-02-01T00:00:00.000Z",
                  long_term_since: "1996-02-01T00:00:00.000Z",
                  projected_lift_date: null,
                  population_estimate: "501 to 1000 people",
                  corrective_measure: "New treatment plant",
                  project_phase: "Construction",
                  latitude: 52.58,
                  longitude: -86.95,
                  source_id: "isc-drinking-water-advisories",
                  source_name: "ISC Long-term Drinking Water Advisories",
                  provenance_url:
                    "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
                  last_refreshed_at: "2026-04-22T00:00:00.000Z",
                  freshness_state: "show",
                  caveat_class: "official_environmental_advisory",
                },
              ],
              meta: {
                summary: {
                  active_advisories: 28,
                  affected_communities: 26,
                },
                source_status: [
                  {
                    source_id: "isc-drinking-water-advisories",
                    source_name: "ISC Long-term Drinking Water Advisories",
                    provenance_url:
                      "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
                    last_refreshed_at: "2026-04-22T00:00:00.000Z",
                    freshness_state: "show",
                  },
                ],
                source_catalog: [
                  buildSourceCatalogRecord({
                    source_id: "isc-drinking-water-advisories",
                    source_name: "ISC Long-term Drinking Water Advisories",
                    provenance_url:
                      "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
                    domain: "environmental_overlay",
                    connector_type: "file_download",
                    access_route: "ISC map data JSON export",
                    update_cadence: "periodic",
                    recommended_usage_mode: "scheduled_ingest",
                    public_methodology_note:
                      "Official ISC data on active long-term drinking water advisories for public systems on reserve in Ontario. This is not a complete map of all Ontario drinking water advisories.",
                    last_refreshed_at: "2026-04-22T00:00:00.000Z",
                  }),
                ],
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
                source_catalog: [
                  buildSourceCatalogRecord({
                    source_id: "osm-aed",
                    source_name: "OpenStreetMap AED",
                    provenance_url: "https://www.openstreetmap.org",
                    domain: "aed",
                    connector_type: "crowdsourced_registry",
                    access_route: "OpenStreetMap export fallback",
                    update_cadence: "ongoing",
                    public_methodology_note:
                      "Crowdsourced AED fallback coverage only.",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                  }),
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
                source_catalog: [
                  buildSourceCatalogRecord({
                    source_id: "mohserlo",
                    source_name: "MOHSERLO",
                    provenance_url: "https://data.ontario.ca/example",
                    domain: "provider_facility",
                    public_methodology_note: "Reference directory only.",
                    last_refreshed_at: "2026-03-27T12:00:00.000Z",
                  }),
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
        "Search for an Ontario facility or share your location to load reference directory results.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Toronto General Hospital"),
    ).not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Union Station AED")).toBeInTheDocument();
    });
    expect(
      screen.getByText(
        "These AED records come from an Ontario fallback path built on OpenStreetMap. Coverage can be incomplete or outdated and should not be treated as a definitive registry.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Crowdsourced")).toBeInTheDocument();
    expect(screen.getByText("Incomplete coverage")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Crowdsourced AED data. Locations may be incomplete or outdated. In an emergency, call 911 immediately.",
      ),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Ontario system context")).toBeInTheDocument();
      expect(screen.getByText("Toronto CACC")).toBeInTheDocument();
      expect(screen.getByText("Dispatch centres")).toBeInTheDocument();
      expect(screen.getByText("Paramedic services")).toBeInTheDocument();
      expect(screen.getByText("CTAS 1")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(
        screen.getByText("Ontario long-term drinking water advisories"),
      ).toBeInTheDocument();
      expect(screen.getByText("Neskantaga First Nation")).toBeInTheDocument();
      expect(screen.getByText("Active advisories")).toBeInTheDocument();
      expect(screen.getByText("Affected communities")).toBeInTheDocument();
    });

    expect(screen.getAllByText("Connector").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Reuse posture").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Approved with conditions").length).toBeGreaterThan(0);
    expect(screen.getByText("Analytics only")).toBeInTheDocument();
    expect(screen.getAllByText("Scheduled ingest").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "Official Ontario ambulance response-time reporting for context only.",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "Official ISC data on active long-term drinking water advisories for public systems on reserve in Ontario. This is not a complete map of all Ontario drinking water advisories.",
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Ontario naloxone kits")).toBeInTheDocument();
    expect(
      screen.getByText("Share your location to request an AQHI snapshot."),
    ).toBeInTheDocument();

    fireEvent.change(
      screen.getByPlaceholderText(
        "Search Ontario hospitals, clinics, or services",
      ),
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

  it("shows the EMS suppression state without breaking the rest of the page", async () => {
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
                source_catalog: [],
              },
            }),
        });
      }

      if (url.includes("/api/resources/system-context")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              data: {
                dispatch_centres: [],
                paramedic_services: [],
              },
              meta: {
                source_status: [
                  {
                    source_id: "ontario-land-ambulance-response-times",
                    source_name: "Ontario Land Ambulance Response Times",
                    provenance_url:
                      "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
                    last_refreshed_at: "2025-01-01T00:00:00.000Z",
                    freshness_state: "suppress",
                  },
                ],
                source_catalog: [
                  buildSourceCatalogRecord({
                    source_id: "ontario-land-ambulance-response-times",
                    source_name: "Ontario Land Ambulance Response Times",
                    provenance_url:
                      "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times",
                    domain: "system_context",
                    recommended_usage_mode: "analytics_only",
                    last_refreshed_at: "2025-01-01T00:00:00.000Z",
                    freshness_state: "suppress",
                  }),
                ],
              },
          }),
        });
      }

      if (url.includes("/api/resources/water-advisories")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              count: 0,
              data: [],
              meta: {
                summary: {
                  active_advisories: 28,
                  affected_communities: 26,
                },
                source_status: [
                  {
                    source_id: "isc-drinking-water-advisories",
                    source_name: "ISC Long-term Drinking Water Advisories",
                    provenance_url:
                      "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
                    last_refreshed_at: "2025-01-01T00:00:00.000Z",
                    freshness_state: "suppress",
                  },
                ],
                source_catalog: [
                  buildSourceCatalogRecord({
                    source_id: "isc-drinking-water-advisories",
                    source_name: "ISC Long-term Drinking Water Advisories",
                    provenance_url:
                      "https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679",
                    domain: "environmental_overlay",
                    connector_type: "file_download",
                    access_route: "ISC map data JSON export",
                    update_cadence: "periodic",
                    recommended_usage_mode: "scheduled_ingest",
                    last_refreshed_at: "2025-01-01T00:00:00.000Z",
                    freshness_state: "suppress",
                  }),
                ],
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
              count: 0,
              data: [],
              meta: {
                source_status: [],
                source_catalog: [],
              },
            }),
        });
      }

      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<ResourcesPage />);

    await waitFor(() => {
      expect(
        screen.getAllByText(
          "Ontario EMS system-context records are temporarily hidden because the source is stale or unavailable.",
        ).length,
      ).toBe(2);
    });

    await waitFor(() => {
      expect(
        screen.getByText(
          "Ontario drinking water advisories are temporarily hidden because the source is stale or unavailable.",
        ),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Ontario AED locations")).toBeInTheDocument();
    expect(screen.getByText("Ontario naloxone kits")).toBeInTheDocument();
  });
});
