import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RegionSelector } from "@/components/RegionSelector";

describe("RegionSelector", () => {
  it("renders all-region option and supplied region options", () => {
    render(
      <RegionSelector
        regions={[
          {
            region_id: "ca-on-region-east",
            region_name: "East Health Region",
            hospital_count: 4,
            reporting_count: 3,
          },
        ]}
        selectedRegionId={null}
        onRegionChange={() => {}}
      />,
    );

    expect(screen.getByText("All Regions")).toBeInTheDocument();
    expect(screen.getByText("East Health Region (3/4)")).toBeInTheDocument();
  });

  it("calls onRegionChange with region id and null for all", () => {
    const onRegionChange = vi.fn();

    render(
      <RegionSelector
        regions={[
          {
            region_id: "ca-on-region-east",
            region_name: "East Health Region",
            hospital_count: 4,
            reporting_count: 4,
          },
        ]}
        selectedRegionId={null}
        onRegionChange={onRegionChange}
      />,
    );

    const select = screen.getByRole("combobox");

    fireEvent.change(select, { target: { value: "ca-on-region-east" } });
    expect(onRegionChange).toHaveBeenCalledWith("ca-on-region-east");

    fireEvent.change(select, { target: { value: "all" } });
    expect(onRegionChange).toHaveBeenCalledWith(null);
  });
});
