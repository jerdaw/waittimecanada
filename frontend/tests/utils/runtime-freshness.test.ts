import { describe, expect, it } from "vitest";
import { resolveHeartbeatStaleThresholdMinutes } from "@/utils/runtime-freshness";

describe("resolveHeartbeatStaleThresholdMinutes", () => {
  it("uses the configured positive threshold", () => {
    expect(resolveHeartbeatStaleThresholdMinutes("45")).toBe(45);
  });

  it.each([undefined, "", "not-a-number", "0", "-10"])(
    "falls back to 120 for invalid input %s",
    (value) => {
      expect(resolveHeartbeatStaleThresholdMinutes(value)).toBe(120);
    },
  );
});
