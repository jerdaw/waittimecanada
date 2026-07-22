import { render, screen } from "@testing-library/react";
import { act } from "react-dom/test-utils";
import { hydrateRoot } from "react-dom/client";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { HeroStats } from "@/components/HeroStats";
import type { PublicCoverage } from "@/types/coverage";

const coverage: PublicCoverage = {
  hospital_count: 399,
  province_count: 4,
  generated_at: "2026-07-20T15:27:00.000Z",
  latest_measurement_at: "2026-07-20T15:26:51.217Z",
};

describe("HeroStats", () => {
  it("renders exact current coverage with meaningful accessibility text", () => {
    render(<HeroStats coverage={coverage} />);

    expect(screen.getByText("4 Provinces")).toBeInTheDocument();
    expect(screen.getByText("399 Hospitals")).toBeInTheDocument();
    expect(screen.getByText("Sources Checked Hourly")).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "4 Provinces. 399 Hospitals. Sources Checked Hourly",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Coverage counts generated from current public data on 2026-07-20.",
      ),
    ).toHaveClass("sr-only");
  });

  it("renders an honest fallback without placeholder leakage", () => {
    const { container } = render(<HeroStats coverage={null} />);

    expect(screen.getByText("Province count unavailable")).toBeInTheDocument();
    expect(screen.getByText("Hospital count unavailable")).toBeInTheDocument();
    expect(container.textContent).not.toContain("...");
    expect(container.textContent).not.toContain("+ Hospitals");
  });

  it("uses identical coverage text for server render and hydration", async () => {
    const serverHtml = renderToString(<HeroStats coverage={coverage} />);
    expect(serverHtml).toContain("399 Hospitals");
    expect(serverHtml).not.toContain("...");

    const container = document.createElement("div");
    container.innerHTML = serverHtml;
    const hydrationErrors: unknown[][] = [];
    const originalError = console.error;
    console.error = (...args: unknown[]) => {
      hydrationErrors.push(args);
    };

    let root: ReturnType<typeof hydrateRoot> | undefined;
    try {
      await act(async () => {
        root = hydrateRoot(container, <HeroStats coverage={coverage} />);
      });
      expect(container.textContent).toContain("399 Hospitals");
      expect(
        hydrationErrors.some((args) =>
          String(args[0]).toLowerCase().includes("hydration"),
        ),
      ).toBe(false);
    } finally {
      await act(async () => {
        root?.unmount();
      });
      console.error = originalError;
    }
  });
});
