import { describe, expect, it } from "vitest";

import { getPublicApiErrorMessage } from "./apiErrors";

describe("getPublicApiErrorMessage", () => {
  it.each([
    new Error("PRIVATE_MARKER database.internal:5432"),
    "PRIVATE_MARKER string failure",
    { detail: "PRIVATE_MARKER object failure" },
    undefined,
  ])("redacts exception details from %o", (error) => {
    const message = getPublicApiErrorMessage(error);

    expect(message).toBe("Internal server error");
    expect(message).not.toContain("PRIVATE_MARKER");
  });
});
