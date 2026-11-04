import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProvinceMethodologyCard } from "@/components/methods/ProvinceMethodologyCard";

describe("ProvinceMethodologyCard", () => {
  it("shows unknown when the database source metadata has no patient scope", () => {
    render(
      <ProvinceMethodologyCard
        source={{
          id: "quebec-msss",
          name: "Québec MSSS",
          province: "Quebec",
          url: "https://example.invalid",
          methodology_url: null,
          default_metric_family: "TIME_TO_PROVIDER",
          default_start_event: "REGISTRATION",
          default_end_event: "PHYSICIAN",
          default_statistic_type: "ROLLING_AVG",
        }}
      />,
    );

    expect(screen.getByText("Patient Scope")).toBeInTheDocument();
    expect(
      screen.getByText("Unknown (not represented in source metadata)"),
    ).toBeInTheDocument();
  });
});
