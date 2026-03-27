import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResourceList } from "@/components/ResourceList";
import type { ResourceRecord } from "@/utils/public-health-hub";

const facilityResources: ResourceRecord[] = [
  {
    id: "facility-1",
    kind: "facility",
    name: "Toronto General Hospital",
    province: "ON",
    city: "Toronto",
    latitude: 43.6532,
    longitude: -79.3832,
    distance_km: 1.2,
    source_id: "mohserlo",
    source_name: "MOHSERLO",
    provenance_url: "https://data.ontario.ca/example",
    last_refreshed_at: "2026-03-27T12:00:00.000Z",
    freshness_state: "show",
    caveat_class: "reference_directory",
    address: "200 Elizabeth St",
    phone: "416-000-0000",
    website_url: "https://example.com",
    reference_status: "directory_only",
    location_description: "Hospital",
  },
];

const aedResources: ResourceRecord[] = [
  {
    id: "aed-1",
    kind: "aed",
    name: "Union Station AED",
    province: "ON",
    city: "Toronto",
    latitude: 43.6453,
    longitude: -79.3806,
    distance_km: 0.6,
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
    access_notes: "public",
  },
];

describe("ResourceList", () => {
  it("renders resource cards with provenance caveat", () => {
    render(<ResourceList resources={facilityResources} />);

    expect(screen.getByText("Toronto General Hospital")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Reference directory data. This is not a live operational status feed.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Source: MOHSERLO")).toBeInTheDocument();
  });

  it("renders crowdsourced AED labels and caveat copy", () => {
    render(<ResourceList resources={aedResources} />);

    expect(screen.getByText("Union Station AED")).toBeInTheDocument();
    expect(screen.getByText("Crowdsourced")).toBeInTheDocument();
    expect(screen.getByText("Incomplete coverage")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Crowdsourced AED data. Locations may be incomplete or outdated. In an emergency, call 911 immediately.",
      ),
    ).toBeInTheDocument();
  });

  it("renders empty state when there are no resources", () => {
    render(<ResourceList resources={[]} emptyTitle="No resources loaded." />);

    expect(screen.getByText("No resources loaded.")).toBeInTheDocument();
  });
});
