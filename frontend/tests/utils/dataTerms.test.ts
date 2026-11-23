import { describe, it, expect } from "vitest";
import {
  DATA_TERMS_HEADER_VALUE,
  DATA_TERMS_NOTICE,
  buildSourceAttributions,
  getSourceDisplayName,
} from "@/utils/dataTerms";

describe("data terms wording", () => {
  it("never claims a data licence", () => {
    for (const text of [DATA_TERMS_NOTICE, DATA_TERMS_HEADER_VALUE]) {
      expect(text).not.toMatch(/CC-BY|creative commons/i);
    }
    expect(DATA_TERMS_NOTICE).toMatch(/own terms/);
  });
});

describe("getSourceDisplayName", () => {
  it("shows Ontario Health for the Ontario source", () => {
    expect(
      getSourceDisplayName("ontario-health", "Health Quality Ontario"),
    ).toBe("Ontario Health");
  });
  it("leaves other sources unchanged", () => {
    expect(getSourceDisplayName("qc", "Quebec MSSS")).toBe("Quebec MSSS");
  });
});

describe("buildSourceAttributions", () => {
  it("returns one entry per source", () => {
    const rows = [
      {
        source_id: "a",
        source_name: "A",
        source_url: "u",
        methodology_url: "m",
      },
      {
        source_id: "a",
        source_name: "A",
        source_url: "u",
        methodology_url: "m",
      },
      { source_id: "b" },
    ];
    expect(buildSourceAttributions(rows)).toEqual([
      {
        source_id: "a",
        source_name: "A",
        source_url: "u",
        methodology_url: "m",
      },
      {
        source_id: "b",
        source_name: null,
        source_url: null,
        methodology_url: null,
      },
    ]);
  });
});
