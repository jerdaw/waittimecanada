import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmergencyBanner } from "../../components/EmergencyBanner";

describe("EmergencyBanner", () => {
  it("renders the warning text", () => {
    render(<EmergencyBanner />);
    expect(screen.getByText(/Emergency\?/i)).toBeInTheDocument();
    expect(screen.getByText(/911/)).toBeInTheDocument();
  });

  it("contains a clickable link to 911", () => {
    render(<EmergencyBanner />);
    const link = screen.getByRole("link", { name: /911/i });
    expect(link).toHaveAttribute("href", "tel:911");
  });
});
