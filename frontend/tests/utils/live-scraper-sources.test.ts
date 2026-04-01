import { describe, expect, it } from "vitest";

import {
  filterActiveLiveSourceRows,
  hasLegacyPublicSourceId,
  isActiveLiveScraperSource,
} from "@/utils/live-scraper-sources";

describe("live-scraper-sources", () => {
  it("accepts only the canonical live source ids", () => {
    expect(isActiveLiveScraperSource("quebec-msss")).toBe(true);
    expect(isActiveLiveScraperSource("ontario-health")).toBe(true);
    expect(isActiveLiveScraperSource("alberta-ahs")).toBe(true);
    expect(isActiveLiveScraperSource("bc-phsa")).toBe(true);
    expect(isActiveLiveScraperSource("manitoba-shared-health")).toBe(false);
    expect(isActiveLiveScraperSource("on-health")).toBe(false);
  });

  it("filters dormant and legacy source rows from aggregate payloads", () => {
    const rows = [
      { source_id: "quebec-msss", source_name: "Quebec MSSS" },
      { source_id: "ontario-health", source_name: "Ontario Health" },
      { source_id: "manitoba-shared-health", source_name: "Manitoba" },
      { source_id: "on-health", source_name: "Legacy Ontario" },
    ];

    expect(filterActiveLiveSourceRows(rows)).toEqual([
      { source_id: "quebec-msss", source_name: "Quebec MSSS" },
      { source_id: "ontario-health", source_name: "Ontario Health" },
    ]);
  });

  it("detects legacy source ids in serialized public payloads", () => {
    expect(
      hasLegacyPublicSourceId(
        JSON.stringify({
          sources: [{ source_id: "manitoba-shared-health" }],
        }),
      ),
    ).toBe(true);
    expect(
      hasLegacyPublicSourceId(
        JSON.stringify({
          sources: [{ source_id: "ontario-health" }],
        }),
      ),
    ).toBe(false);
  });
});
