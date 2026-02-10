import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ViewToggle } from "../../components/ViewToggle";

describe("ViewToggle", () => {
  it("renders all toggle options", () => {
    render(<ViewToggle mode="map" onChange={() => {}} />);
    expect(screen.getByText("List")).toBeInTheDocument();
    expect(screen.getByText("Map")).toBeInTheDocument();
    expect(screen.getByText("Split")).toBeInTheDocument();
  });

  it("highlights the active mode", () => {
    render(<ViewToggle mode="list" onChange={() => {}} />);
    // Text is now inside a span, so we need to find the parent button
    const listBtn = screen.getByText("List").closest("button");
    expect(listBtn?.className).toContain("bg-background");
    expect(listBtn?.className).toContain("shadow-sm");

    const mapBtn = screen.getByText("Map").closest("button");
    expect(mapBtn?.className).not.toContain("shadow-sm");
  });

  it("calls onChange when clicked", () => {
    const onChange = vi.fn();
    render(<ViewToggle mode="map" onChange={onChange} />);

    fireEvent.click(screen.getByText("List"));
    expect(onChange).toHaveBeenCalledWith("list");

    fireEvent.click(screen.getByText("Split"));
    expect(onChange).toHaveBeenCalledWith("split");
  });
});
