import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AboutSection } from "@/components/AboutSection";

describe("AboutSection", () => {
  it("renders with expanded view by default", () => {
    render(<AboutSection />);

    expect(
      screen.getByRole("heading", { name: /Wait Time Canada/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/About This Project/i)).toBeInTheDocument();

    // Content should be visible when expanded by default
    expect(
      screen.getByText(/As a pre-medical student/i),
    ).toBeInTheDocument();
  });

  it("collapses to hide narrative when clicked", () => {
    render(<AboutSection />);

    const button = screen.getByRole("button", {
      name: /collapse about section/i,
    });
    fireEvent.click(button);

    // Content should no longer be visible
    expect(
      screen.queryByText(/As a pre-medical student/i),
    ).not.toBeInTheDocument();
  });

  it("re-expands when clicked again", () => {
    render(<AboutSection />);

    const button = screen.getByRole("button");

    // Collapse
    fireEvent.click(button);
    expect(
      screen.queryByText(/As a pre-medical student/i),
    ).not.toBeInTheDocument();

    // Re-expand
    fireEvent.click(button);
    expect(screen.getByText(/As a pre-medical student/i)).toBeInTheDocument();
  });

  it("displays author information when expanded", () => {
    render(<AboutSection />);

    // Expanded by default — no click needed
    expect(screen.getByText(/Jeremy Dawson/i)).toBeInTheDocument();
    // Use getAllByText since "Pre-Medical Student" appears in the narrative too
    const premedText = screen.getAllByText(/Pre-Medical Student/i);
    expect(premedText.length).toBeGreaterThan(0);
  });

  it("renders social links when expanded", () => {
    render(<AboutSection />);

    // Expanded by default — no click needed
    const githubLink = screen.getByLabelText(/view on github/i);
    const linkedinLink = screen.getByLabelText(/linkedin profile/i);
    const emailLink = screen.getByLabelText(/email contact/i);

    expect(githubLink).toHaveAttribute(
      "href",
      "https://github.com/jerdaw/waittimecanada",
    );
    expect(linkedinLink).toHaveAttribute(
      "href",
      "https://linkedin.com/in/jeremyjdawson",
    );
    expect(emailLink).toHaveAttribute("href", "mailto:jeremyjdawson@gmail.com");
  });

  it("has proper accessibility attributes", () => {
    render(<AboutSection />);

    const button = screen.getByRole("button");

    // Should start expanded
    expect(button).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("opens external links in new tab with security attributes", () => {
    render(<AboutSection />);

    // Expanded by default — no click needed
    const githubLink = screen.getByLabelText(/view on github/i);
    const linkedinLink = screen.getByLabelText(/linkedin profile/i);

    expect(githubLink).toHaveAttribute("target", "_blank");
    expect(githubLink).toHaveAttribute("rel", "noopener noreferrer");
    expect(linkedinLink).toHaveAttribute("target", "_blank");
    expect(linkedinLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("emphasizes key concepts in the narrative", () => {
    render(<AboutSection />);

    // Expanded by default — no click needed
    const strongElements = screen.getAllByText(
      /completely different methodologies|Wait Time Canada is different/i,
    );
    expect(strongElements.length).toBeGreaterThan(0);
  });
});
