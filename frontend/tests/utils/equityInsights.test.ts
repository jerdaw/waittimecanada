import { describe, expect, it } from "vitest";
import { computeEquityLinkageSummary } from "@/utils/equityInsights";
import type { EquityFeatureCollection } from "@/utils/equity";

describe("computeEquityLinkageSummary", () => {
  it("excludes quintile 0 tracts from low-income linkage counts", () => {
    const hospitals = [
      {
        hospital_id: "h1",
        latitude: 43.65,
        longitude: -79.38,
        period_mean: 100,
      },
      {
        hospital_id: "h2",
        latitude: 43.75,
        longitude: -79.48,
        period_mean: 120,
      },
    ];

    const equityData: EquityFeatureCollection = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          id: "t0",
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [-79.39, 43.64],
                [-79.37, 43.64],
                [-79.37, 43.66],
                [-79.39, 43.66],
                [-79.39, 43.64],
              ],
            ],
          },
          properties: {
            tract_id: "t0",
            tract_name: "No Data Tract",
            income_quintile: 0,
            median_household_income: null,
            is_placeholder: false,
          },
        },
        {
          type: "Feature",
          id: "t1",
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [-79.49, 43.74],
                [-79.47, 43.74],
                [-79.47, 43.76],
                [-79.49, 43.76],
                [-79.49, 43.74],
              ],
            ],
          },
          properties: {
            tract_id: "t1",
            tract_name: "Low Income Tract",
            income_quintile: 1,
            median_household_income: 40000,
            is_placeholder: false,
          },
        },
      ],
    };

    const result = computeEquityLinkageSummary(hospitals, equityData, 30);
    expect(result.low_income_tracts).toBe(1);
    expect(result.hospitals_near_low_income).toBe(2);
    expect(result.sensitivity_analysis.length).toBeGreaterThanOrEqual(4);
    expect(
      result.sensitivity_analysis.some((item) => item.threshold_km === 30),
    ).toBe(true);
    expect(result.uncertainty.method).toBe("bootstrap_percentile");
    expect(result.uncertainty.near_low_income_avg_wait_ci95.lower).not.toBeNull();
    expect(result.uncertainty.near_low_income_avg_wait_ci95.upper).not.toBeNull();
    expect(result.uncertainty.wait_gap_minutes_ci95.lower).not.toBeNull();
    expect(result.uncertainty.wait_gap_minutes_ci95.upper).not.toBeNull();
  });

  it("supports multipolygon tract geometry", () => {
    const hospitals = [
      {
        hospital_id: "h1",
        latitude: 45.41,
        longitude: -75.69,
        period_mean: 90,
      },
    ];

    const equityData: EquityFeatureCollection = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          id: "mp1",
          geometry: {
            type: "MultiPolygon",
            coordinates: [
              [
                [
                  [-75.7, 45.4],
                  [-75.68, 45.4],
                  [-75.68, 45.42],
                  [-75.7, 45.42],
                  [-75.7, 45.4],
                ],
              ],
            ],
          },
          properties: {
            tract_id: "mp1",
            tract_name: "MultiPolygon Tract",
            income_quintile: 2,
            median_household_income: 55000,
            is_placeholder: false,
          },
        },
      ],
    };

    const result = computeEquityLinkageSummary(hospitals, equityData, 10);
    expect(result.low_income_tracts).toBe(1);
    expect(result.hospitals_near_low_income).toBe(1);
    expect(result.uncertainty.near_low_income_avg_wait_ci95.lower).toBeNull();
    expect(result.uncertainty.wait_gap_minutes_ci95.lower).toBeNull();
  });
});
