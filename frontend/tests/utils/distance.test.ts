import { describe, it, expect } from "vitest";
import { calculateDistance } from "@/utils/distance";

describe("calculateDistance", () => {
  it("calculates distance between Toronto and Ottawa correctly", () => {
    // Toronto (approx)
    const lat1 = 43.6532;
    const lon1 = -79.3832;

    // Ottawa (approx)
    const lat2 = 45.4215;
    const lon2 = -75.6972;

    const distance = calculateDistance(lat1, lon1, lat2, lon2);

    // Expected distance is approx 350-400km
    expect(distance).toBeGreaterThan(300);
    expect(distance).toBeLessThan(450);
  });

  it("returns 0 for same point", () => {
    expect(calculateDistance(45, -75, 45, -75)).toBe(0);
  });
});
