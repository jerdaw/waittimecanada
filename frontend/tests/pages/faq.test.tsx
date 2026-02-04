import { render, screen } from "@testing-library/react";
import FAQPage from "@/app/faq/page";
import { describe, it, expect, vi } from "vitest";

// Mock Header because it uses Link and ViewToggle which uses router
vi.mock("@/components/Header", () => ({
  Header: () => <header data-testid="mock-header">Header</header>,
}));

// Mock JSON-LD output to avoid error with script tag in JSDOM?
// No, JSDOM handles script tags fine mostly.

describe("FAQPage", () => {
  it("renders page title and description", () => {
    render(<FAQPage />);
    expect(screen.getByText("Frequently Asked Questions")).toBeInTheDocument();
    expect(screen.getByText(/Understand how we track wait times/)).toBeInTheDocument();
    expect(screen.getByTestId("mock-header")).toBeInTheDocument();
  });

  it("renders faq items", () => {
    render(<FAQPage />);
    expect(screen.getByText("Are these wait times official?")).toBeInTheDocument();
    expect(screen.getByText("Why do wait times change so quickly?")).toBeInTheDocument();
  });

  it("renders methodology link", () => {
    render(<FAQPage />);
    const link = screen.getByText("View Methodology");
    expect(link).toHaveAttribute("href", "/methods");
  });
});
