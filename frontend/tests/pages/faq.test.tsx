import { render, screen } from "@testing-library/react";
import FAQPage from "@/app/[locale]/faq/page";
import { describe, it, expect, vi } from "vitest";

// Mock Header because it uses Link and ViewToggle which uses router
vi.mock("@/components/Header", () => ({
  Header: () => <header data-testid="mock-header">Header</header>,
}));

// Mock Footer
vi.mock("@/components/Footer", () => ({
  Footer: () => <footer data-testid="mock-footer">Footer</footer>,
}));

describe("FAQPage", () => {
  it("renders page title and description", async () => {
    const Page = await FAQPage();
    render(Page);
    expect(screen.getByText("Frequently Asked Questions")).toBeInTheDocument();
    expect(
      screen.getByText(/Understand how we track wait times/),
    ).toBeInTheDocument();
    expect(screen.getByTestId("mock-header")).toBeInTheDocument();
  });

  it("renders faq items", async () => {
    const Page = await FAQPage();
    render(Page);
    expect(
      screen.getByText("Are these wait times official?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Why do wait times change so quickly?"),
    ).toBeInTheDocument();
  });

  it("renders methodology link", async () => {
    const Page = await FAQPage();
    render(Page);
    const link = screen.getByText("View Methodology");
    expect(link).toHaveAttribute("href", "/methods");
  });
});
