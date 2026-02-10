import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { EquityLegend } from "@/components/EquityLegend";

describe("EquityLegend", () => {
  it("renders quintile labels", () => {
    render(<EquityLegend />);

    expect(screen.getByText("Income Quintile")).toBeInTheDocument();
    expect(screen.getByText("Lowest 20%")).toBeInTheDocument();
    expect(screen.getByText("Highest 20%")).toBeInTheDocument();
  });

  it("shows placeholder notice when metadata indicates scaffold", () => {
    render(
      <EquityLegend
        metadata={{
          province: "ON",
          source: "test",
          attribution: "test attribution",
          generated_at: "2026-02-08T00:00:00.000Z",
          is_placeholder: true,
          note: "test note",
        }}
      />,
    );

    expect(screen.getByText("test attribution")).toBeInTheDocument();
    expect(screen.getByText(/Placeholder layer/)).toBeInTheDocument();
  });
});
