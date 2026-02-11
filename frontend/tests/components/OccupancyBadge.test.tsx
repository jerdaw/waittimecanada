import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { OccupancyBadge } from "@/components/OccupancyBadge";

describe("OccupancyBadge", () => {
  it("renders percentage value", () => {
    render(<OccupancyBadge percentage={95.5} />);
    expect(screen.getByText("96%")).toBeInTheDocument();
  });

  it("rounds percentage to nearest integer", () => {
    render(<OccupancyBadge percentage={110.4} />);
    expect(screen.getByText("110%")).toBeInTheDocument();
  });

  it("applies success color for occupancy below 90%", () => {
    const { container } = render(<OccupancyBadge percentage={85} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-success");
    expect(badge.className).toContain("text-success");
  });

  it("applies warning color for occupancy between 90-110%", () => {
    const { container } = render(<OccupancyBadge percentage={95} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-warning");
    expect(badge.className).toContain("text-warning");
  });

  it("applies danger color for occupancy above 110%", () => {
    const { container } = render(<OccupancyBadge percentage={127} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-danger");
    expect(badge.className).toContain("text-danger");
  });

  it("shows overcrowded message in title for high occupancy", () => {
    const { container } = render(<OccupancyBadge percentage={150} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.title).toContain("Overcrowded");
    expect(badge.title).toContain("150%");
  });

  it("shows normal message in title for low occupancy", () => {
    const { container } = render(<OccupancyBadge percentage={85} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.title).not.toContain("Overcrowded");
    expect(badge.title).toContain("85%");
  });

  it("applies small size by default", () => {
    const { container } = render(<OccupancyBadge percentage={100} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("text-[10px]");
  });

  it("applies medium size when specified", () => {
    const { container } = render(<OccupancyBadge percentage={100} size="md" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("text-xs");
  });

  it("applies custom className", () => {
    const { container } = render(
      <OccupancyBadge percentage={100} className="custom-class" />,
    );
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("custom-class");
  });

  it("animates pulse for overcrowded state", () => {
    const { container } = render(<OccupancyBadge percentage={120} />);
    const badge = container.firstChild as HTMLElement;
    const indicators = badge.querySelectorAll("span");
    // First span is the indicator dot
    const indicator = indicators[0] as HTMLElement;
    expect(indicator.className).toContain("animate-pulse");
  });

  it("does not animate for normal occupancy", () => {
    const { container } = render(<OccupancyBadge percentage={80} />);
    const badge = container.firstChild as HTMLElement;
    const indicators = badge.querySelectorAll("span");
    const indicator = indicators[0] as HTMLElement;
    expect(indicator.className).not.toContain("animate-pulse");
  });

  it("handles edge case at 90% threshold", () => {
    const { container } = render(<OccupancyBadge percentage={90} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-warning");
  });

  it("handles edge case at 110% threshold", () => {
    const { container } = render(<OccupancyBadge percentage={110} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-warning");
  });

  it("handles edge case just above 110%", () => {
    const { container } = render(<OccupancyBadge percentage={110.1} />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-danger");
  });
});
