import { describe, expect, it } from "vitest";

import {
  areMethodologiesComparable,
  buildUniquePairwiseComparisons,
  generateDivergenceBrief,
  getComparabilityDimensions,
  getComparabilityLevel,
  getComparabilityMatchCount,
  type Methodology,
  type MethodologySource,
} from "@/utils/comparability";

describe("comparability utility", () => {
  const comparableMethodology: Methodology = {
    metric_family: "TIME_TO_PROVIDER",
    start_event: "TRIAGE",
    end_event: "PHYSICIAN",
    statistic_type: "MEAN",
  };

  it("treats identical methodologies as directly comparable", () => {
    expect(
      areMethodologiesComparable(comparableMethodology, {
        ...comparableMethodology,
      }),
    ).toBe(true);
  });

  it("counts field-by-field ontology matches", () => {
    const partialMethodology: Methodology = {
      metric_family: "TIME_TO_PROVIDER",
      start_event: "REGISTRATION",
      end_event: "PHYSICIAN",
      statistic_type: "ROLLING_AVG",
    };

    expect(
      getComparabilityMatchCount(comparableMethodology, partialMethodology),
    ).toBe(2);
  });

  it("returns explicit field verdicts for each ontology dimension", () => {
    const dimensions = getComparabilityDimensions(comparableMethodology, {
      metric_family: "TOTAL_LOS",
      start_event: "TRIAGE",
      end_event: "DISCHARGE",
      statistic_type: "P90",
    });

    expect(dimensions).toEqual([
      expect.objectContaining({ key: "metric_family", matches: false }),
      expect.objectContaining({ key: "start_event", matches: true }),
      expect.objectContaining({ key: "end_event", matches: false }),
      expect.objectContaining({ key: "statistic_type", matches: false }),
    ]);
  });

  it("classifies source pairs by overall comparability level", () => {
    const ontario: MethodologySource = {
      id: "ontario-health",
      name: "Health Quality Ontario",
      province: "Ontario",
      default_metric_family: "TIME_TO_PROVIDER",
      default_start_event: "TRIAGE",
      default_end_event: "PHYSICIAN",
      default_statistic_type: "MEAN",
    };
    const bc: MethodologySource = {
      id: "bc-phsa",
      name: "BC PHSA",
      province: "British Columbia",
      default_metric_family: "TIME_TO_PROVIDER",
      default_start_event: "TRIAGE",
      default_end_event: "PHYSICIAN",
      default_statistic_type: "P90",
    };
    const quebec: MethodologySource = {
      id: "quebec-msss",
      name: "Quebec MSSS",
      province: "Quebec",
      default_metric_family: "TIME_TO_PROVIDER",
      default_start_event: "REGISTRATION",
      default_end_event: "PHYSICIAN",
      default_statistic_type: "ROLLING_AVG",
    };

    expect(getComparabilityLevel(ontario, bc)).toBe("partial");
    expect(getComparabilityLevel(ontario, quebec)).toBe("partial");
  });

  it("builds a divergence brief from the real mismatch set", () => {
    const brief = generateDivergenceBrief(comparableMethodology, {
      metric_family: "TIME_TO_PROVIDER",
      start_event: "REGISTRATION",
      end_event: "PHYSICIAN",
      statistic_type: "ROLLING_AVG",
    });

    expect(brief).toContain("REGISTRATION");
    expect(brief).toContain("ROLLING_AVG");
    expect(brief).toContain("Methodology Divergence");
  });

  it("returns all unique province pairs for the methods matrix verdict section", () => {
    const pairs = buildUniquePairwiseComparisons([
      {
        id: "ontario-health",
        name: "Health Quality Ontario",
        province: "Ontario",
        default_metric_family: "TIME_TO_PROVIDER",
        default_start_event: "TRIAGE",
        default_end_event: "PHYSICIAN",
        default_statistic_type: "MEAN",
      },
      {
        id: "bc-phsa",
        name: "BC PHSA",
        province: "British Columbia",
        default_metric_family: "TIME_TO_PROVIDER",
        default_start_event: "TRIAGE",
        default_end_event: "PHYSICIAN",
        default_statistic_type: "P90",
      },
      {
        id: "quebec-msss",
        name: "Quebec MSSS",
        province: "Quebec",
        default_metric_family: "TIME_TO_PROVIDER",
        default_start_event: "REGISTRATION",
        default_end_event: "PHYSICIAN",
        default_statistic_type: "ROLLING_AVG",
      },
    ]);

    expect(pairs).toHaveLength(3);
    expect(pairs[0]).toMatchObject({
      left: expect.objectContaining({ province: "Ontario" }),
      right: expect.objectContaining({ province: "British Columbia" }),
    });
  });
});
