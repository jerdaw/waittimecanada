import { render, screen } from "@testing-library/react";
import { ExpandedCardDetails } from "@/components/ExpandedCardDetails";
import { vi } from "vitest";

const mockHospital = {
  id: "test-hospital",
  name: "Test Hospital",
  city: "Toronto",
  province: "ON",
  lat: 43.65,
  lon: -79.38,
  current_wait_time: 120,
  last_updated: new Date().toISOString(),
  telehealth_number: "1-866-555-0123",
  website_url: "https://example.com"
};

describe("ExpandedCardDetails", () => {
  it("renders methodology metrics", () => {
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText("Triage to Doctor")).toBeInTheDocument();
  });

  it("renders telehealth number if available", () => {
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText("1-866-555-0123")).toBeInTheDocument();
  });

  it("renders quick action buttons", () => {
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText("Directions")).toBeInTheDocument();
    expect(screen.getByText("Website")).toBeInTheDocument();
    expect(screen.getByText("Call")).toBeInTheDocument();
  });

  it("shows live data indicator for fresh data", () => {
    render(<ExpandedCardDetails hospital={mockHospital} />);
    expect(screen.getByText("Live Data")).toBeInTheDocument();
  });

  it("shows stale data indicator for old data", () => {
    const staleHospital = {
      ...mockHospital,
      last_updated: new Date(Date.now() - 3600000).toISOString() // 1 hour ago
    };
    render(<ExpandedCardDetails hospital={staleHospital} />);
    expect(screen.getByText("Stale Data")).toBeInTheDocument();
  });
});
