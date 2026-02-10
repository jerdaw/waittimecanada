import { describe, it, expect } from "vitest";

// Test the comparability logic that's duplicated in multiple places
describe("Comparability Logic", () => {
  interface Methodology {
    metric_family: string;
    start_event: string;
    end_event: string;
    statistic_type: string;
  }

  function areComparable(a: Methodology, b: Methodology): boolean {
    return (
      a.metric_family === b.metric_family &&
      a.start_event === b.start_event &&
      a.end_event === b.end_event &&
      a.statistic_type === b.statistic_type
    );
  }

  function generateDivergenceBrief(
    a: Methodology,
    b: Methodology,
  ): string | null {
    if (areComparable(a, b)) return null;

    const differences: string[] = [];

    if (a.metric_family !== b.metric_family) {
      differences.push(
        `Different metrics: ${a.metric_family} vs ${b.metric_family}`,
      );
    }
    if (a.start_event !== b.start_event) {
      differences.push(
        `Different start points: ${a.start_event} vs ${b.start_event}`,
      );
    }
    if (a.end_event !== b.end_event) {
      differences.push(
        `Different end points: ${a.end_event} vs ${b.end_event}`,
      );
    }
    if (a.statistic_type !== b.statistic_type) {
      differences.push(
        `Different statistics: ${a.statistic_type} vs ${b.statistic_type}`,
      );
    }

    return (
      "Methodology Divergence: Direct comparison is scientifically invalid. " +
      differences.join("; ") +
      "."
    );
  }

  describe("areComparable", () => {
    it("returns true for identical methodologies", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = { ...a };

      expect(areComparable(a, b)).toBe(true);
    });

    it("returns false if metric_family differs", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        ...a,
        metric_family: "TOTAL_LOS",
      };

      expect(areComparable(a, b)).toBe(false);
    });

    it("returns false if start_event differs", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        ...a,
        start_event: "REGISTRATION",
      };

      expect(areComparable(a, b)).toBe(false);
    });

    it("returns false if end_event differs", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        ...a,
        end_event: "PROVIDER",
      };

      expect(areComparable(a, b)).toBe(false);
    });

    it("returns false if statistic_type differs", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        ...a,
        statistic_type: "MEDIAN",
      };

      expect(areComparable(a, b)).toBe(false);
    });

    it("returns false if multiple dimensions differ", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        metric_family: "TOTAL_LOS",
        start_event: "REGISTRATION",
        end_event: "DISCHARGE",
        statistic_type: "MEDIAN",
      };

      expect(areComparable(a, b)).toBe(false);
    });
  });

  describe("generateDivergenceBrief", () => {
    it("returns null for comparable methodologies", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = { ...a };

      expect(generateDivergenceBrief(a, b)).toBeNull();
    });

    it("explains single difference", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        ...a,
        start_event: "REGISTRATION",
      };

      const brief = generateDivergenceBrief(a, b);

      expect(brief).toContain("TRIAGE vs REGISTRATION");
      expect(brief).toContain("Methodology Divergence");
    });

    it("explains multiple differences", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        ...a,
        start_event: "REGISTRATION",
        statistic_type: "ROLLING_AVG",
      };

      const brief = generateDivergenceBrief(a, b);

      expect(brief).toContain("TRIAGE vs REGISTRATION");
      expect(brief).toContain("P90 vs ROLLING_AVG");
      expect(brief).toContain(";"); // Multiple differences separated
    });

    it("includes all four dimensions when all differ", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        metric_family: "TOTAL_LOS",
        start_event: "REGISTRATION",
        end_event: "DISCHARGE",
        statistic_type: "MEDIAN",
      };

      const brief = generateDivergenceBrief(a, b);

      expect(brief).toContain("TIME_TO_PROVIDER vs TOTAL_LOS");
      expect(brief).toContain("TRIAGE vs REGISTRATION");
      expect(brief).toContain("PHYSICIAN vs DISCHARGE");
      expect(brief).toContain("P90 vs MEDIAN");
    });

    it("formats message consistently", () => {
      const a: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const b: Methodology = {
        ...a,
        statistic_type: "MEDIAN",
      };

      const brief = generateDivergenceBrief(a, b);

      expect(brief).toMatch(/^Methodology Divergence:/);
      expect(brief).toMatch(/scientifically invalid/);
      expect(brief).toMatch(/\.$/); // Ends with period
    });
  });

  describe("Real-world scenarios", () => {
    it("Ontario vs Quebec (incompatible)", () => {
      const ontario: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const quebec: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "REGISTRATION",
        end_event: "PHYSICIAN",
        statistic_type: "ROLLING_AVG",
      };

      expect(areComparable(ontario, quebec)).toBe(false);

      const brief = generateDivergenceBrief(ontario, quebec);
      expect(brief).toContain("TRIAGE vs REGISTRATION");
      expect(brief).toContain("P90 vs ROLLING_AVG");
    });

    it("Ontario vs Alberta (compatible)", () => {
      const ontario: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const alberta: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      expect(areComparable(ontario, alberta)).toBe(true);
      expect(generateDivergenceBrief(ontario, alberta)).toBeNull();
    });

    it("Two Toronto hospitals (compatible)", () => {
      const torontoGeneral: Methodology = {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
      };

      const torontoWestern: Methodology = { ...torontoGeneral };

      expect(areComparable(torontoGeneral, torontoWestern)).toBe(true);
      expect(
        generateDivergenceBrief(torontoGeneral, torontoWestern),
      ).toBeNull();
    });
  });
});
