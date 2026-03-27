import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AQHICard } from "@/components/AQHICard";
import type { AQHIRecord, SourceStatusRecord } from "@/utils/public-health-hub";

const aqhi: AQHIRecord = {
  location_name: "Toronto",
  aqhi_value: 5,
  category: "moderate",
  issued_at: "2026-03-27T12:00:00.000Z",
  valid_until: "2026-03-27T13:00:00.000Z",
  source_id: "aqhi-geomet",
  source_name: "AQHI GeoMet",
  provenance_url:
    "https://api.weather.gc.ca/collections/aqhi-forecasts-realtime",
  last_refreshed_at: "2026-03-27T12:00:00.000Z",
  freshness_state: "show",
  caveat_class: "official_forecast",
};

const suppressedSourceStatus: SourceStatusRecord = {
  source_id: "aqhi-geomet",
  source_name: "AQHI GeoMet",
  provenance_url:
    "https://api.weather.gc.ca/collections/aqhi-forecasts-realtime",
  last_refreshed_at: "2026-03-25T10:00:00.000Z",
  freshness_state: "suppress",
};

describe("AQHICard", () => {
  it("renders aqhi data", () => {
    render(<AQHICard aqhi={aqhi} />);

    expect(screen.getByText("Toronto")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("moderate")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Official AQHI forecast from Environment and Climate Change Canada. Conditions may change.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Forecast valid until:/)).toBeInTheDocument();
  });

  it("renders location prompt when location is required", () => {
    render(<AQHICard aqhi={null} requiresLocation />);

    expect(
      screen.getByText("Share your location to request an AQHI snapshot."),
    ).toBeInTheDocument();
  });

  it("renders suppressed-state copy when source freshness hides data", () => {
    render(<AQHICard aqhi={null} sourceStatus={suppressedSourceStatus} />);

    expect(
      screen.getByText(
        "This information is currently hidden because freshness or source requirements are not being met.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Last refreshed:/)).toBeInTheDocument();
  });
});
