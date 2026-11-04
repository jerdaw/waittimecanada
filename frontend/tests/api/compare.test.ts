import { describe, expect, it } from "vitest";
import {
  areMethodologiesComparable,
  generateDivergenceBrief,
  type Methodology,
} from "@/utils/comparability";

describe("Comparison utility used by the API", () => {
  const allPatients: Methodology = {
    metric_family: "TIME_TO_PROVIDER",
    start_event: "TRIAGE",
    end_event: "PHYSICIAN",
    statistic_type: "P90",
    patient_scope: "ALL",
  };

  it("accepts matching recorded tags as a screening result", () => {
    expect(areMethodologiesComparable(allPatients, { ...allPatients })).toBe(
      true,
    );
  });

  it("rejects any recorded-dimension mismatch", () => {
    expect(
      areMethodologiesComparable(allPatients, {
        ...allPatients,
        start_event: "REGISTRATION",
      }),
    ).toBe(false);
  });

  it("returns no divergence brief when all recorded tags match", () => {
    expect(generateDivergenceBrief(allPatients, { ...allPatients })).toBeNull();
  });

  it("explains a patient-scope-only mismatch", () => {
    const nonPriorityPatients: Methodology = {
      ...allPatients,
      patient_scope: "NON_PRIORITY",
    };

    expect(areMethodologiesComparable(allPatients, nonPriorityPatients)).toBe(
      false,
    );
    expect(generateDivergenceBrief(allPatients, nonPriorityPatients)).toContain(
      "Different patient scopes: ALL vs NON_PRIORITY",
    );
  });
});
