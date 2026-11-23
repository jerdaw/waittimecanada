import { render, screen } from "@testing-library/react";
import { ExpandedCardDetails } from "@/components/ExpandedCardDetails";
import { vi } from "vitest";

vi.mock("@/components/BenchmarkCard", () => ({
  BenchmarkCard: () => <div>Benchmark Mock</div>,
}));
vi.mock("@/components/TemporalPatterns", () => ({
  TemporalPatterns: () => <div>Temporal Patterns Mock</div>,
}));

const mockHospital = {
  id: "test-hospital",
  name: "Test Hospital",
  city: "Toronto",
  province: "ON",
  latitude: 43.65,
  longitude: -79.38,
  is_verified: true,
  is_visible: true,
  source_id: "test-source",
  current_wait_time: 120,
  wait_time_status: "current" as const,
  last_updated: new Date().toISOString(),
  telehealth_number: "1-866-555-0123",
};

describe("ExpandedCardDetails", () => {
  it("renders methodology metrics", () => {
    // @ts-ignore
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText("Triage to Doctor")).toBeInTheDocument();
  });

  it("renders telehealth number if available", () => {
    // @ts-ignore
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText(/1-866-555-0123/)).toBeInTheDocument();
  });

  it("renders quick action buttons", () => {
    // @ts-ignore
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText(/Directions/i)).toBeInTheDocument();
    // Website button removed
    expect(screen.getByText(/Call Health Info/i)).toBeInTheDocument();
  });

  it("shows live data indicator for fresh data", () => {
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText("Live Data")).toBeInTheDocument();
  });

  it("shows no current data and the last report date for a stale value", () => {
    const staleHospital = {
      ...mockHospital,
      current_wait_time: undefined,
      wait_time_status: "stale" as const,
      last_updated: "2026-06-04T23:33:00.000Z",
    };
    render(<ExpandedCardDetails hospital={staleHospital} />);
    expect(screen.queryByText("Live Data")).not.toBeInTheDocument();
    expect(screen.getAllByText("No current data").length).toBeGreaterThan(0);
    expect(screen.getByText(/Last reported .*2026/)).toBeInTheDocument();
  });

  it("labels Ontario as a monthly average with a source link, never live", () => {
    const ontario = {
      ...mockHospital,
      source_id: "ontario-health",
      current_wait_time: undefined,
      monthly_average_minutes: 30,
      wait_time_status: "monthly" as const,
    };
    render(<ExpandedCardDetails hospital={ontario} />);
    expect(screen.queryByText("Live Data")).not.toBeInTheDocument();
    expect(screen.getAllByText("Monthly average").length).toBeGreaterThan(0);
    expect(screen.getByText(/^Last checked /)).toBeInTheDocument();
    expect(
      screen.getByText(/not the period the figure covers/),
    ).toBeInTheDocument();
    // No reporting period is shown or invented.
    expect(
      screen.getByText(/reporting period is not shown/i),
    ).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /View source/ });
    expect(link).toHaveAttribute(
      "href",
      expect.stringContaining("ontariohealth.ca"),
    );
  });

  it("fails closed when the freshness status is missing", () => {
    const { wait_time_status: _omit, ...withoutStatus } = mockHospital;
    void _omit;
    render(<ExpandedCardDetails hospital={withoutStatus} />);
    expect(screen.queryByText("Live Data")).not.toBeInTheDocument();
  });
});
