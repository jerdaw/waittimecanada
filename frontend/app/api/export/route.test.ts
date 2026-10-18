import { NextRequest } from "next/server";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock the db util
vi.mock("@/utils/db", () => {
  return {
    getDb: vi.fn(),
  };
});

// Mock the cache util
vi.mock("@/utils/cache", () => {
  return {
    NO_STORE_HEADERS: { "Cache-Control": "no-store" },
  };
});

import { getDb } from "@/utils/db";
import { GET } from "./route";

describe("GET /api/export", () => {
  let mockSql: any;

  beforeEach(() => {
    mockSql = vi.fn();
    mockSql.typed = vi.fn((value: string, type: number) => ({
      __sqlTypedParameter: true,
      value,
      type,
    }));
    (getDb as any).mockClear();
    (getDb as any).mockReturnValue(mockSql);
  });

  function createRequest(url: string) {
    const req = new NextRequest(new URL(url, "http://localhost"));
    return req;
  }

  function useFragmentAwareSql(resultSets: Record<string, unknown>[][]) {
    mockSql.mockImplementation(
      (strings: TemplateStringsArray, ...values: any[]) => {
        const fragment = {
          __sqlFragment: true,
          strings: Array.from(strings),
          values,
        };
        if (strings.join("").includes("SELECT")) {
          return Promise.resolve(resultSets.shift() ?? []);
        }
        return fragment;
      },
    );
  }

  function flattenSql(strings: string[], values: any[]): string {
    return strings.reduce((query, part, index) => {
      const value = values[index];
      const renderedValue: string = value?.__sqlFragment
        ? flattenSql(value.strings, value.values)
        : value === undefined
          ? ""
          : " ? ";
      return `${query}${part}${renderedValue}`;
    }, "");
  }

  function flattenSqlParameters(values: any[]): unknown[] {
    return values.flatMap((value) =>
      value?.__sqlFragment ? flattenSqlParameters(value.values) : [value],
    );
  }

  function flattenSqlValues(values: any[]): unknown[] {
    return flattenSqlParameters(values).map((value: any) =>
      value?.__sqlTypedParameter ? value.value : value,
    );
  }

  function makeRawRow(
    id = "1",
    timestamp = "2026-03-01T12:00:00.123456Z",
    overrides: Record<string, unknown> = {},
  ) {
    return {
      export_cursor_id: id,
      export_cursor_timestamp: timestamp,
      timestamp_utc: timestamp,
      hospital_id: "ca-on-test",
      hospital_name: "Test Hospital",
      province: "ON",
      city: "Toronto",
      latitude: 43.7,
      longitude: -79.4,
      wait_time_minutes: 30,
      metric_family: "TIME_TO_PROVIDER",
      start_event: "TRIAGE",
      end_event: "PHYSICIAN",
      statistic_type: "MEAN",
      patient_scope: "ALL",
      source_id: "historical-measurement-source",
      source_name: "Measurement Source Catalog Label",
      methodology_url: "https://example.com/methodology",
      raw_payload_hash: "a".repeat(64),
      parser_version: "v1.2",
      ...overrides,
    };
  }

  function getSelectCalls() {
    return mockSql.mock.calls.filter(([queryStrings]: [TemplateStringsArray]) =>
      queryStrings.join("").includes("SELECT"),
    );
  }

  function getSelectQueries() {
    return getSelectCalls().map(
      ([strings, ...values]: [TemplateStringsArray, ...any[]]) =>
        flattenSql(Array.from(strings), values),
    );
  }

  function getSelectQuery() {
    return getSelectQueries()[0];
  }

  function getSelectValues(index = 0) {
    const [, ...values] = getSelectCalls()[index];
    return flattenSqlValues(values);
  }

  function expectSelectLimit(expected: number) {
    expect(getSelectQuery()).toMatch(/LIMIT\s+\?\s*$/);
    expect(getSelectValues().at(-1)).toBe(expected);
  }

  function makeCursorWithId(cursorToken: string, id: string) {
    const cursor = JSON.parse(
      Buffer.from(cursorToken, "base64url").toString("utf8"),
    );
    cursor.id = id;
    return Buffer.from(JSON.stringify(cursor)).toString("base64url");
  }

  it("exports measurement-level provenance in JSON, without raw snippets", async () => {
    // Attribute source metadata via the stored measurement source, not the
    // hospital's potentially changed current mapping.
    useFragmentAwareSql([[makeRawRow()]]);

    const response = await GET(
      createRequest(
        "/api/export?format=json&include_methodology=false&province=ON&start_date=2026-03-01T00:00:00Z&end_date=2026-03-02T00:00:00Z",
      ),
    );
    const json = await response.json();
    const query = getSelectQuery();

    expect(response.status).toBe(200);
    expect(json.data[0]).toMatchObject({
      source_id: "historical-measurement-source",
      source_name: "Measurement Source Catalog Label",
      methodology_url: "https://example.com/methodology",
      raw_payload_hash: "a".repeat(64),
      parser_version: "v1.2",
    });
    expect(json.data[0]).not.toHaveProperty("raw_payload_snippet");
    expect(query).toContain("m.source_id");
    expect(query).toContain("JOIN sources s ON m.source_id = s.id");
    expect(query).toContain("m.raw_payload_hash");
    expect(query).toContain("m.parser_version");
    expect(query).not.toContain("raw_payload_snippet");
    expect(query).not.toContain("JOIN sources s ON h.source_id = s.id");
    expect(query).toContain("WHERE h.is_verified = true");
    expect(query).toContain("AND h.province =");
    expect(query).toContain("AND m.timestamp_utc >=");
    expect(query).toContain("AND m.timestamp_utc <=");
    expect(query).toContain("ORDER BY m.timestamp_utc DESC, m.id DESC");
    expectSelectLimit(10001);
    expect(json.data[0]).not.toHaveProperty("export_cursor_id");
    expect(json.data[0]).not.toHaveProperty("export_cursor_timestamp");
    expect(json.metadata).toMatchObject({
      page_size: 10000,
      record_count: 1,
      has_more: false,
      is_complete: true,
      next_cursor: null,
      next_url: null,
    });
  });

  it("exports measurement provenance columns in CSV even when methodology is omitted", async () => {
    useFragmentAwareSql([[makeRawRow()]]);

    const response = await GET(
      createRequest("/api/export?format=csv&include_methodology=false"),
    );
    const records = (await response.text()).trim().split("\n");
    const headers = records[0].split(",");
    const values = records[1].split(",");
    const exportedRow = Object.fromEntries(
      headers.map((header, index) => [header, values[index]]),
    );

    expect(exportedRow).toMatchObject({
      source_id: "historical-measurement-source",
      source_name: "Measurement Source Catalog Label",
      methodology_url: "https://example.com/methodology",
      raw_payload_hash: "a".repeat(64),
      parser_version: "v1.2",
    });
    expect(headers).not.toContain("raw_payload_snippet");
  });

  it("reports raw CSV page metadata and a same-filter next link", async () => {
    useFragmentAwareSql([[makeRawRow("9"), makeRawRow("8")]]);

    const response = await GET(
      createRequest("/api/export?format=csv&page_size=1&province=ON"),
    );
    const csv = await response.text();
    const link = response.headers.get("link");

    expect(response.status).toBe(200);
    expect(response.headers.get("x-export-record-count")).toBe("1");
    expect(response.headers.get("x-export-page-size")).toBe("1");
    expect(response.headers.get("x-export-has-more")).toBe("true");
    expect(response.headers.get("x-export-complete")).toBe("false");
    expect(response.headers.get("x-export-next-cursor")).toBeTruthy();
    expect(link).toMatch(/^<\/api\/export\?/);
    expect(link).toContain("province=ON");
    expect(link).toContain("page_size=1");
    expect(link).toContain("cursor=");
    expect(csv.split("\n")).toHaveLength(2);
    expect(csv).not.toContain("raw_payload_snippet");
    expectSelectLimit(2);
  });

  it("preserves null provenance values without synthesizing replacements", async () => {
    const row = makeRawRow("7", undefined, {
      raw_payload_hash: null,
      parser_version: null,
    });
    useFragmentAwareSql([[row]]);

    const jsonResponse = await GET(createRequest("/api/export?format=json"));
    const json = await jsonResponse.json();

    expect(json.data[0].raw_payload_hash).toBeNull();
    expect(json.data[0].parser_version).toBeNull();

    useFragmentAwareSql([[row]]);
    const csvResponse = await GET(createRequest("/api/export?format=csv"));
    const [headerLine, valueLine] = (await csvResponse.text())
      .trim()
      .split("\n");
    const headers = headerLine.split(",");
    const values = valueLine.split(",");
    const exportedRow = Object.fromEntries(
      headers.map((header, index) => [header, values[index]]),
    );

    expect(exportedRow.raw_payload_hash).toBe("");
    expect(exportedRow.parser_version).toBe("");
  });

  it("does not expose per-measurement provenance on aggregate exports", async () => {
    useFragmentAwareSql([
      [
        {
          period_start: "2026-03-01T00:00:00Z",
          period_end: "2026-03-02T00:00:00Z",
          hospital_id: "ca-on-test",
          hospital_name: "Test Hospital",
          province: "ON",
          mean_wait_minutes: 30,
          sample_count: 3,
          metric_family: "TIME_TO_PROVIDER",
          start_event: "TRIAGE",
          end_event: "PHYSICIAN",
          statistic_type: "MEAN",
          source_id: "aggregate-source",
          methodology_url: "https://example.com/methodology",
        },
      ],
    ]);

    const response = await GET(
      createRequest("/api/export?format=json&granularity=daily"),
    );
    const json = await response.json();
    const query = getSelectQuery();

    expect(json.metadata.data_type).toBe("aggregated");
    expect(json.data[0]).not.toHaveProperty("raw_payload_hash");
    expect(json.data[0]).not.toHaveProperty("parser_version");
    expect(query).not.toContain("raw_payload_hash");
    expect(query).not.toContain("parser_version");
    expect(json.metadata).not.toHaveProperty("page_size");
    expect(response.headers.get("x-export-record-count")).toBeNull();
  });

  it("returns a bounded first page from a result set larger than 10,000 rows", async () => {
    const queriedRows = Array.from({ length: 10001 }, (_, index) =>
      makeRawRow(
        String(10001 - index),
        `2026-03-01T12:00:00.${String(999999 - index).padStart(6, "0")}Z`,
        { source_id: String(10001 - index) },
      ),
    );
    useFragmentAwareSql([queriedRows]);

    const response = await GET(createRequest("/api/export?format=json"));
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.data).toHaveLength(10000);
    expect(json.data[0].hospital_id).toBe("ca-on-test");
    expect(json.data.at(-1).source_id).toBe("2");
    expect(json.data.map((row: any) => row.source_id)).not.toContain("1");
    expect(json.metadata).toMatchObject({
      record_count: 10000,
      page_size: 10000,
      has_more: true,
      is_complete: false,
    });
    expect(typeof json.metadata.next_cursor).toBe("string");
    expect(json.metadata.next_url).toContain("cursor=");
    expectSelectLimit(10001);
  });

  it("continues after tied timestamps using exact microseconds and bigint-safe IDs", async () => {
    const rows = [
      makeRawRow("9007199254740993", "2026-03-01T12:00:00.123456Z"),
      makeRawRow("9007199254740992", "2026-03-01T12:00:00.123456Z"),
      makeRawRow("9007199254740991", "2026-03-01T12:00:00.123455Z"),
    ];
    useFragmentAwareSql([rows]);

    const firstResponse = await GET(
      createRequest("/api/export?format=json&page_size=2&province=ON"),
    );
    const firstPage = await firstResponse.json();
    const cursor = JSON.parse(
      Buffer.from(firstPage.metadata.next_cursor, "base64url").toString("utf8"),
    );

    expect(firstPage.data).toHaveLength(2);
    expect(cursor).toMatchObject({
      id: "9007199254740992",
      timestamp: "2026-03-01T12:00:00.123456Z",
    });
    expectSelectLimit(3);

    mockSql.mockClear();
    useFragmentAwareSql([[rows[2]]]);
    const secondResponse = await GET(
      createRequest(
        `/api/export?format=json&page_size=2&province=ON&cursor=${encodeURIComponent(firstPage.metadata.next_cursor)}`,
      ),
    );
    const secondPage = await secondResponse.json();
    const secondQuery = getSelectQuery();

    expect(secondPage.data).toHaveLength(1);
    expect(secondPage.data[0].timestamp_utc).toBe(
      "2026-03-01T12:00:00.123455Z",
    );
    expect(secondPage.metadata.has_more).toBe(false);
    expect(secondQuery).toContain("(m.timestamp_utc, m.id) <");
    expect(getSelectValues()).toContain("2026-03-01T12:00:00.123456Z");
    expect(getSelectValues()).toContain("9007199254740992");
    expectSelectLimit(3);
    expect(secondQuery).toContain("ORDER BY m.timestamp_utc DESC, m.id DESC");
  });

  it.each([
    ["minimum bigint", "-9223372036854775808"],
    ["zero", "0"],
    ["maximum bigint", "9223372036854775807"],
  ])("accepts %s cursor IDs as decimal strings", async (_label, id) => {
    useFragmentAwareSql([[makeRawRow("1"), makeRawRow("0")]]);
    const first = await GET(
      createRequest("/api/export?format=json&page_size=1"),
    );
    const firstPage = await first.json();
    const validBoundaryCursor = makeCursorWithId(
      firstPage.metadata.next_cursor,
      id,
    );

    mockSql.mockClear();
    useFragmentAwareSql([[]]);
    const response = await GET(
      createRequest(
        `/api/export?format=json&page_size=1&cursor=${encodeURIComponent(validBoundaryCursor)}`,
      ),
    );

    expect(response.status).toBe(200);
    expect(getSelectValues()).toContain(id);
  });

  it.each([
    ["above maximum", "9223372036854775808"],
    ["below minimum", "-9223372036854775809"],
    ["non-canonical negative zero", "-0"],
  ])("rejects %s cursor IDs before querying", async (_label, id) => {
    useFragmentAwareSql([[makeRawRow("1"), makeRawRow("0")]]);
    const first = await GET(
      createRequest("/api/export?format=json&page_size=1"),
    );
    const firstPage = await first.json();
    const invalidCursor = makeCursorWithId(firstPage.metadata.next_cursor, id);

    (getDb as any).mockClear();
    mockSql.mockClear();
    const response = await GET(
      createRequest(
        `/api/export?format=json&page_size=1&cursor=${encodeURIComponent(invalidCursor)}`,
      ),
    );

    expect(response.status).toBe(400);
    expect(getDb).not.toHaveBeenCalled();
  });

  it("rejects malformed and filter-mismatched cursors before querying", async () => {
    (getDb as any).mockClear();
    const malformed = await GET(
      createRequest("/api/export?format=json&cursor=not-a-valid-token!"),
    );
    expect(malformed.status).toBe(400);
    expect(getDb).not.toHaveBeenCalled();

    useFragmentAwareSql([[makeRawRow("1"), makeRawRow("0")]]);
    const first = await GET(
      createRequest("/api/export?format=json&page_size=1&province=ON"),
    );
    const firstPage = await first.json();
    (getDb as any).mockClear();

    const mismatched = await GET(
      createRequest(
        `/api/export?format=json&page_size=1&province=QC&cursor=${encodeURIComponent(firstPage.metadata.next_cursor)}`,
      ),
    );

    expect(mismatched.status).toBe(400);
    expect(getDb).not.toHaveBeenCalled();
  });

  it("rejects pagination parameters for aggregate exports and leaves aggregate queries unchanged", async () => {
    const invalid = await GET(
      createRequest("/api/export?granularity=daily&page_size=2&format=json"),
    );
    expect(invalid.status).toBe(400);
    expect(getDb).not.toHaveBeenCalled();

    useFragmentAwareSql([
      [
        {
          period_start: "2026-03-01T00:00:00Z",
          period_end: "2026-03-02T00:00:00Z",
          hospital_id: "ca-on-test",
          hospital_name: "Test Hospital",
          province: "ON",
          mean_wait_minutes: 30,
          sample_count: 3,
          metric_family: "TIME_TO_PROVIDER",
          start_event: "TRIAGE",
          end_event: "PHYSICIAN",
          statistic_type: "MEAN",
          source_id: "aggregate-source",
          methodology_url: "https://example.com/methodology",
        },
      ],
    ]);
    const aggregate = await GET(
      createRequest("/api/export?granularity=daily&format=json"),
    );
    const json = await aggregate.json();

    expect(aggregate.status).toBe(200);
    expect(json.metadata).not.toHaveProperty("page_size");
    expect(aggregate.headers.get("x-export-has-more")).toBeNull();
    expect(getSelectQuery()).toContain("LIMIT 10000");
  });

  it("includes methodology_homogeneity in JSON metadata for raw export", async () => {
    const mockResults = [
      {
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "P90",
        value: 120,
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(200);
    expect(json.metadata.methodology_homogeneity).toBeDefined();
    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(true);
    expect(
      json.metadata.methodology_homogeneity.distinct_methodology_groups,
    ).toBe(1);
    expect(json.metadata.methodology_homogeneity.groups).toHaveLength(1);
    expect(json.metadata.methodology_homogeneity.groups[0].record_count).toBe(
      1,
    );
  });

  it("marks is_homogeneous=true when all records share same methodology", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(true);
    expect(
      json.metadata.methodology_homogeneity.distinct_methodology_groups,
    ).toBe(1);
    expect(json.metadata.methodology_homogeneity.groups[0].record_count).toBe(
      2,
    );
  });

  it("marks is_homogeneous=false and lists groups when mixed methodology", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
      {
        metric_family: "X",
        start_event: "Y",
        end_event: "Z",
        statistic_type: "W",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=json");
    const res = await GET(req);
    const json = await res.json();

    expect(json.metadata.methodology_homogeneity.is_homogeneous).toBe(false);
    expect(
      json.metadata.methodology_homogeneity.distinct_methodology_groups,
    ).toBe(2);
    expect(json.metadata.methodology_homogeneity.groups).toHaveLength(2);
    expect(json.metadata.methodology_homogeneity.divergence_note).toContain(
      "scientifically invalid",
    );
  });

  it("does not include methodology_homogeneity in CSV response", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=csv");
    const res = await GET(req);
    const text = await res.text();

    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(res.headers.get("x-methodology-divergence")).toBe("false");
    expect(res.headers.get("x-methodology-groups")).toBe("1");
    expect(text).not.toContain("METHODOLOGY DIVERGENCE WARNING");
  });

  it("adds diverange warning comment to raw CSV when methodology is mixed", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
      },
      {
        metric_family: "X",
        start_event: "Y",
        end_event: "Z",
        statistic_type: "W",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest("/api/export?format=csv");
    const res = await GET(req);
    const text = await res.text();

    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(res.headers.get("x-methodology-divergence")).toBe("true");
    expect(res.headers.get("x-methodology-groups")).toBe("2");
    expect(text.split("\n")[0]).toContain("# METHODOLOGY DIVERGENCE WARNING");
    expect(text.split("\n")[0]).toContain("scientifically invalid");
  });

  it("adds diverange warning comment to aggregated CSV when methodology is mixed", async () => {
    const mockResults = [
      {
        metric_family: "A",
        start_event: "B",
        end_event: "C",
        statistic_type: "D",
        period_start: "2026-01-01",
      },
      {
        metric_family: "X",
        start_event: "Y",
        end_event: "Z",
        statistic_type: "W",
        period_start: "2026-01-02",
      },
    ];
    mockSql.mockResolvedValue(mockResults);

    const req = createRequest(
      "/api/export?format=csv&granularity=daily&include_methodology=true",
    );
    const res = await GET(req);
    const text = await res.text();

    expect(res.headers.get("content-type")).toContain("text/csv");
    expect(res.headers.get("x-methodology-divergence")).toBe("true");
    expect(res.headers.get("x-methodology-groups")).toBe("2");
    expect(text.split("\n")[0]).toContain("# METHODOLOGY DIVERGENCE WARNING");
  });

  it("rejects hourly exports larger than 30 days", async () => {
    const req = createRequest(
      "/api/export?granularity=hourly&start_date=2026-01-01T00:00:00Z&end_date=2026-02-15T00:00:00Z",
    );
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(400);
    expect(json.error).toBe("Hourly export window too large");
    expect(mockSql).not.toHaveBeenCalled();
  });

  it("serves bounded hourly exports from raw measurements", async () => {
    mockSql.mockResolvedValue([
      {
        period_start: "2026-03-01T12:00:00Z",
        period_end: "2026-03-01T13:00:00Z",
        hospital_id: "ca-on-test",
        hospital_name: "Test Hospital",
        province: "ON",
        city: "Toronto",
        latitude: 43.7,
        longitude: -79.4,
        mean_wait_minutes: 120,
        median_wait_minutes: 115,
        p90_wait_minutes: 150,
        min_wait_minutes: 90,
        max_wait_minutes: 180,
        sample_count: 4,
        std_dev: 20,
        metric_family: "TIME_TO_PROVIDER",
        start_event: "TRIAGE",
        end_event: "PHYSICIAN",
        statistic_type: "MEAN",
        source_id: "ontario-health",
        methodology_url: "https://example.com/method",
      },
    ]);

    const req = createRequest(
      "/api/export?granularity=hourly&format=json&start_date=2026-03-01T00:00:00Z&end_date=2026-03-10T00:00:00Z",
    );
    const res = await GET(req);
    const json = await res.json();

    expect(res.status).toBe(200);
    expect(json.metadata.granularity).toBe("hourly");
    expect(json.metadata.data_type).toBe("aggregated");
    expect(json.data).toHaveLength(1);
  });

  it("redacts server details when export queries fail", async () => {
    (getDb as any).mockImplementationOnce(() => {
      throw new Error("PRIVATE_MARKER export database detail");
    });

    const res = await GET(createRequest("/api/export?format=json"));
    const json = await res.json();

    expect(res.status).toBe(500);
    expect(json.error).toBe("Failed to export data");
    expect(json.message).toBe("Internal server error");
    expect(JSON.stringify(json)).not.toContain("PRIVATE_MARKER");
  });
});
