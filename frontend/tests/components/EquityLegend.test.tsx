import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { EquityLegend } from "@/components/EquityLegend";

describe("EquityLegend", () => {
  it("renders quintile labels including no-data", () => {
    render(<EquityLegend />);

    expect(screen.getByText("Income Quintile")).toBeInTheDocument();
    expect(screen.getByText("No Data")).toBeInTheDocument();
    expect(screen.getByText("Lowest 20%")).toBeInTheDocument();
    expect(screen.getByText("Highest 20%")).toBeInTheDocument();
    expect(
      screen.getByText(/Open Government Licence - Canada/i),
    ).toBeInTheDocument();
  });

  it("renders custom attribution from metadata", () => {
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
        interpretationNote="Descriptive only"
        temporalNote="Income year 2021"
      />,
    );

    expect(screen.getByText("test attribution")).toBeInTheDocument();
    expect(screen.getByText("Descriptive only")).toBeInTheDocument();
    expect(screen.getByText("Income year 2021")).toBeInTheDocument();
    expect(screen.queryByText(/Placeholder layer/)).not.toBeInTheDocument();
  });
});
