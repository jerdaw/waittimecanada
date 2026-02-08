import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { EquityLayerToggle } from "@/components/EquityLayerToggle";

describe("EquityLayerToggle", () => {
  it("renders disabled state and toggles on", () => {
    const onChange = vi.fn();
    render(<EquityLayerToggle enabled={false} onChange={onChange} />);

    const button = screen.getByRole("button", { name: "Enable income overlay" });
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it("renders loading hint when loading", () => {
    render(<EquityLayerToggle enabled={true} loading={true} onChange={() => undefined} />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });
});
