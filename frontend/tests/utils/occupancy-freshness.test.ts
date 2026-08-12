import { describe, expect, it } from "vitest";
import { isCurrentOccupancyAvailable } from "@/utils/occupancy-freshness";

const NOW = Date.parse("2026-08-12T13:00:00.000Z");

function currentInput() {
  return {
    hasObservations: true,
    latestObservation: "2026-08-12T12:30:00.000Z",
    sourceStatus: "healthy",
    sourceLastRun: "2026-08-12T12:40:00.000Z",
    consecutiveFailures: 0,
  };
}

describe("isCurrentOccupancyAvailable", () => {
  it("keeps fresh occupancy from a healthy source available", () => {
    expect(isCurrentOccupancyAvailable(currentInput(), 120, NOW)).toBe(true);
  });

  it("fails closed when the source collector is reporting an error", () => {
    expect(
      isCurrentOccupancyAvailable(
        {
          ...currentInput(),
          sourceStatus: "error",
          consecutiveFailures: 24,
        },
        120,
        NOW,
      ),
    ).toBe(false);
  });

  it("fails closed when the latest observation exceeds the public threshold", () => {
    expect(
      isCurrentOccupancyAvailable(
        {
          ...currentInput(),
          latestObservation: "2026-08-12T10:59:59.000Z",
        },
        120,
        NOW,
      ),
    ).toBe(false);
  });

  it("honours a shorter resolved threshold", () => {
    expect(isCurrentOccupancyAvailable(currentInput(), 20, NOW)).toBe(false);
  });

  it("fails closed for future observations or heartbeats", () => {
    expect(
      isCurrentOccupancyAvailable(
        {
          ...currentInput(),
          latestObservation: "2026-08-12T13:00:01.000Z",
        },
        120,
        NOW,
      ),
    ).toBe(false);
    expect(
      isCurrentOccupancyAvailable(
        {
          ...currentInput(),
          sourceLastRun: "2026-08-12T13:00:01.000Z",
        },
        120,
        NOW,
      ),
    ).toBe(false);
  });
});
