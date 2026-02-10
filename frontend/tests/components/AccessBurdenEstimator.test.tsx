import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AccessBurdenEstimator } from "@/components/AccessBurdenEstimator";

describe("AccessBurdenEstimator", () => {
  it("renders with collapsed view showing estimate range", () => {
    render(
      <AccessBurdenEstimator
        distanceKm={20}
        province="ON"
        hospitalType="urban"
      />,
    );

    expect(screen.getByText(/Access Burden Estimate/i)).toBeInTheDocument();
    // Should show a cost range
    expect(screen.getByText(/\$\d+ - \$\d+/)).toBeInTheDocument();
  });

  it("displays prominent disclaimer about not delaying care", () => {
    render(
      <AccessBurdenEstimator
        distanceKm={20}
        province="ON"
        hospitalType="urban"
      />,
    );

    expect(
      screen.getByText(/Never delay emergency care for cost/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Call 911 for emergencies/i)).toBeInTheDocument();
  });

  it("expands to show detailed breakdown when clicked", () => {
    render(
      <AccessBurdenEstimator
        distanceKm={20}
        province="ON"
        hospitalType="urban"
      />,
    );

    const button = screen.getByRole("button", {
      name: /expand access burden details/i,
    });
    fireEvent.click(button);

    expect(screen.getByText(/round trip/i)).toBeInTheDocument();
    expect(screen.getByText(/Parking \(urban hospital\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Estimated Total/i)).toBeInTheDocument();
  });

  it("collapses when clicked again", () => {
    render(
      <AccessBurdenEstimator
        distanceKm={20}
        province="ON"
        hospitalType="urban"
      />,
    );

    const button = screen.getByRole("button");

    // Expand
    fireEvent.click(button);
    expect(screen.getByText(/round trip/i)).toBeInTheDocument();

    // Collapse
    fireEvent.click(button);
    expect(screen.queryByText(/round trip/i)).not.toBeInTheDocument();
  });

  describe("fuel cost calculation", () => {
    it("calculates fuel cost correctly for Ontario", () => {
      // 20km × 2 (round trip) × 10L/100km × $1.55/L = $6.20
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText("$6.20")).toBeInTheDocument();
    });

    it("uses correct gas price for British Columbia", () => {
      // 20km × 2 (round trip) × 10L/100km × $1.75/L = $7.00
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="BC"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText("$7.00")).toBeInTheDocument();
    });

    it("uses correct gas price for Alberta", () => {
      // 20km × 2 (round trip) × 10L/100km × $1.45/L = $5.80
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="AB"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText("$5.80")).toBeInTheDocument();
    });

    it("calculates round trip distance correctly", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={15.5}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText(/31 km round trip/i)).toBeInTheDocument();
    });
  });

  describe("parking estimates", () => {
    it("shows urban parking range", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText(/\$15 - \$25/)).toBeInTheDocument();
    });

    it("shows suburban parking range", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="suburban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText(/\$10 - \$15/)).toBeInTheDocument();
    });

    it("shows rural parking range", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="rural"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText(/\$0 - \$5/)).toBeInTheDocument();
    });
  });

  describe("total cost calculation", () => {
    it("calculates correct total range for urban hospital", () => {
      // Fuel: $6.20, Parking: $15-$25 → Total: $21-$31 (rounded to $21-$31)
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );

      const totalText = screen.getByText(/\$21 - \$31/);
      expect(totalText).toBeInTheDocument();
    });

    it("calculates correct total range for rural hospital", () => {
      // Fuel: $6.20, Parking: $0-$5 → Total: $6-$11
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="rural"
        />,
      );

      const totalText = screen.getByText(/\$6 - \$11/);
      expect(totalText).toBeInTheDocument();
    });
  });

  describe("methodology information", () => {
    it("displays fuel consumption rate", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText(/10L\/100km/i)).toBeInTheDocument();
    });

    it("displays gas price with province code", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText(/\$1.55\/L \(ON\)/i)).toBeInTheDocument();
    });

    it("explains why this feature exists", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      expect(screen.getByText(/Why show this\?/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Financial barriers.*often invisible/i),
      ).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("has proper aria attributes", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );

      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-expanded", "false");

      fireEvent.click(button);
      expect(button).toHaveAttribute("aria-expanded", "true");
    });

    it("has descriptive aria-label", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ON"
          hospitalType="urban"
        />,
      );

      expect(
        screen.getByRole("button", { name: /expand access burden details/i }),
      ).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button"));
      expect(
        screen.getByRole("button", { name: /collapse access burden details/i }),
      ).toBeInTheDocument();
    });
  });

  describe("edge cases", () => {
    it("handles very short distances", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={0.5}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      // 0.5km × 2 = 1km round trip
      expect(screen.getByText(/1 km round trip/i)).toBeInTheDocument();
    });

    it("handles unknown province with default gas price", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={20}
          province="ZZ"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      // Should use default $1.55/L → $6.20
      expect(screen.getByText("$6.20")).toBeInTheDocument();
    });

    it("handles very long distances", () => {
      render(
        <AccessBurdenEstimator
          distanceKm={150}
          province="ON"
          hospitalType="urban"
        />,
      );
      fireEvent.click(screen.getByRole("button"));

      // 150km × 2 = 300km round trip
      expect(screen.getByText(/300 km round trip/i)).toBeInTheDocument();
    });
  });
});
