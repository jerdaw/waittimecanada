import { describe, expect, it } from "vitest";
import {
  LIVE_ESTIMATE_STALE_THRESHOLD_MINUTES,
  classifyWaitTime,
  getLiveEstimateStaleThresholdMinutes,
  isMeasurementWithinThreshold,
  isMonthlySource,
} from "@/utils/wait-time-freshness";
import { DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES } from "@/utils/live-scraper-sources";

const NOW = Date.parse("2026-11-23T12:00:00Z");
const MIN = 60 * 1000;
const minutesAgo = (m: number) => new Date(NOW - m * MIN).toISOString();

describe("wait-time freshness thresholds", () => {
  it("reuses the existing hourly-cadence heartbeat threshold for live sources", () => {
    for (const sourceId of ["alberta-ahs", "bc-phsa", "quebec-msss"]) {
      expect(LIVE_ESTIMATE_STALE_THRESHOLD_MINUTES[sourceId]).toBe(
        DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES,
      );
    }
    expect(DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES).toBe(120);
  });

  it("falls back to the default for unknown or missing sources", () => {
    expect(getLiveEstimateStaleThresholdMinutes("mystery")).toBe(120);
    expect(getLiveEstimateStaleThresholdMinutes(undefined)).toBe(120);
    expect(getLiveEstimateStaleThresholdMinutes(null)).toBe(120);
  });

  it("identifies monthly sources", () => {
    expect(isMonthlySource("ontario-health")).toBe(true);
    for (const id of ["bc-phsa", "alberta-ahs", "quebec-msss", "", null]) {
      expect(isMonthlySource(id)).toBe(false);
    }
  });
});

describe("isMeasurementWithinThreshold boundaries", () => {
  it("is current exactly at the threshold and stale one millisecond after", () => {
    expect(isMeasurementWithinThreshold(minutesAgo(120), 120, NOW)).toBe(true);
    expect(
      isMeasurementWithinThreshold(
        new Date(NOW - 120 * MIN - 1).toISOString(),
        120,
        NOW,
      ),
    ).toBe(false);
  });

  it("is current for a fresh measurement and at zero age", () => {
    expect(isMeasurementWithinThreshold(minutesAgo(0), 120, NOW)).toBe(true);
    expect(isMeasurementWithinThreshold(minutesAgo(119), 120, NOW)).toBe(true);
    expect(isMeasurementWithinThreshold(minutesAgo(121), 120, NOW)).toBe(false);
  });

  it("rejects missing, invalid and future timestamps", () => {
    expect(isMeasurementWithinThreshold(null, 120, NOW)).toBe(false);
    expect(isMeasurementWithinThreshold(undefined, 120, NOW)).toBe(false);
    expect(isMeasurementWithinThreshold("not a date", 120, NOW)).toBe(false);
    expect(isMeasurementWithinThreshold(minutesAgo(-5), 120, NOW)).toBe(false);
  });

  it("accepts Date and epoch values", () => {
    expect(isMeasurementWithinThreshold(new Date(NOW - MIN), 120, NOW)).toBe(
      true,
    );
    expect(isMeasurementWithinThreshold(NOW - MIN, 120, NOW)).toBe(true);
  });
});

describe("classifyWaitTime", () => {
  it.each(["alberta-ahs", "bc-phsa", "quebec-msss"])(
    "%s: current at 120 minutes, stale at 121",
    (sourceId) => {
      const base = { sourceId, hasValue: true };
      expect(
        classifyWaitTime({ ...base, latestMeasurement: minutesAgo(120) }, NOW),
      ).toBe("current");
      expect(
        classifyWaitTime({ ...base, latestMeasurement: minutesAgo(121) }, NOW),
      ).toBe("stale");
    },
  );

  it("treats the Fraser Health June values as stale", () => {
    expect(
      classifyWaitTime(
        {
          sourceId: "bc-phsa",
          hasValue: true,
          latestMeasurement: "2026-06-04T23:33:00Z",
        },
        NOW,
      ),
    ).toBe("stale");
  });

  it("treats the Quebec 11 August values as stale", () => {
    expect(
      classifyWaitTime(
        {
          sourceId: "quebec-msss",
          hasValue: true,
          latestMeasurement: "2026-08-11T12:00:00Z",
        },
        NOW,
      ),
    ).toBe("stale");
  });

  it("never classifies Ontario as current, even for a measurement from just now", () => {
    expect(
      classifyWaitTime(
        {
          sourceId: "ontario-health",
          hasValue: true,
          latestMeasurement: minutesAgo(0),
        },
        NOW,
      ),
    ).toBe("monthly");
    expect(
      classifyWaitTime(
        {
          sourceId: "ontario-health",
          hasValue: true,
          latestMeasurement: "2026-01-31T00:00:00Z",
        },
        NOW,
      ),
    ).toBe("monthly");
  });

  it("fails closed for an unknown source with an old value", () => {
    expect(
      classifyWaitTime(
        {
          sourceId: undefined,
          hasValue: true,
          latestMeasurement: minutesAgo(500),
        },
        NOW,
      ),
    ).toBe("stale");
  });

  it("is stale when a value has no usable timestamp", () => {
    expect(
      classifyWaitTime(
        { sourceId: "bc-phsa", hasValue: true, latestMeasurement: null },
        NOW,
      ),
    ).toBe("stale");
  });

  it("returns none without a value", () => {
    expect(
      classifyWaitTime(
        {
          sourceId: "bc-phsa",
          hasValue: false,
          latestMeasurement: minutesAgo(1),
        },
        NOW,
      ),
    ).toBe("none");
  });
});
