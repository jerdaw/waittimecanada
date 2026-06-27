import { describe, expect, it } from "vitest";
import { getDatabaseSslOption } from "@/utils/db";

describe("getDatabaseSslOption", () => {
  it("disables SSL for localhost databases by default", () => {
    expect(getDatabaseSslOption("postgresql://localhost:5432/test")).toBe(
      false,
    );
    expect(getDatabaseSslOption("postgresql://127.0.0.1:5432/test")).toBe(
      false,
    );
    expect(getDatabaseSslOption("postgresql://[::1]:5432/test")).toBe(false);
  });

  it("requires SSL for hosted databases by default", () => {
    expect(getDatabaseSslOption("postgresql://example.com:5432/test")).toBe(
      "require",
    );
  });

  it("honors explicit SSL mode overrides", () => {
    expect(
      getDatabaseSslOption("postgresql://localhost:5432/test", "require"),
    ).toBe("require");
    expect(
      getDatabaseSslOption("postgresql://example.com:5432/test", "disable"),
    ).toBe(false);
  });
});
