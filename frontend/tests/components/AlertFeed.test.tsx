import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AlertFeed } from "@/components/AlertFeed";
import type { AlertRecord } from "@/utils/public-health-hub";

const alerts: AlertRecord[] = [
  {
    id: "alert-1",
    title: "Example medical device recall",
    summary: "A sample recall used for testing.",
    alert_type: "medical_device",
    published_at: "2026-03-27T09:00:00.000Z",
    updated_at: "2026-03-27T10:15:00.000Z",
    source_id: "health-canada-recalls",
    source_name: "Health Canada Recalls and Safety Alerts",
    provenance_url: "https://recalls-rappels.canada.ca/en",
    last_refreshed_at: "2026-03-27T12:00:00.000Z",
    freshness_state: "show",
    caveat_class: "official_alert_feed",
    affected_products: [{ brand_name: "Example Device", din: "12345678" }],
  },
];

describe("AlertFeed", () => {
  it("renders alert cards with source metadata", () => {
    render(<AlertFeed alerts={alerts} />);

    expect(
      screen.getByText("Example medical device recall"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("A sample recall used for testing."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Source: Health Canada Recalls and Safety Alerts"),
    ).toBeInTheDocument();
  });

  it("renders empty state when there are no alerts", () => {
    render(<AlertFeed alerts={[]} emptyTitle="No alerts right now." />);

    expect(screen.getByText("No alerts right now.")).toBeInTheDocument();
  });
});
