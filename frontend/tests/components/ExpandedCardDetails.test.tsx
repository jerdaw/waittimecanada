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

  it("shows stale data indicator for old data", () => {
    const staleHospital = {
      ...mockHospital,
      last_updated: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    };
    render(<ExpandedCardDetails hospital={staleHospital} />);
    expect(screen.getByText("Stale Data")).toBeInTheDocument();
  });
});
