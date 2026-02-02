import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DivergenceWarning } from "@/components/DivergenceWarning";

describe("DivergenceWarning", () => {
  const testMessage = "Methodology Divergence: Different start points.";

  describe("compact variant", () => {
    it("renders compact warning with icon", () => {
      render(<DivergenceWarning message={testMessage} variant="compact" />);

      expect(screen.getByText("Different methodologies")).toBeInTheDocument();
    });

    it("applies compact styling", () => {
      const { container } = render(
        <DivergenceWarning message={testMessage} variant="compact" />
      );

      const element = container.firstChild as HTMLElement;
      expect(element).toHaveClass("inline-flex");
      expect(element).toHaveClass("bg-amber-100");
    });
  });

  describe("inline variant", () => {
    it("renders full message text", () => {
      render(<DivergenceWarning message={testMessage} variant="inline" />);

      expect(screen.getByText(testMessage)).toBeInTheDocument();
    });

    it("includes warning icon", () => {
      const { container } = render(
        <DivergenceWarning message={testMessage} variant="inline" />
      );

      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });
  });

  describe("banner variant", () => {
    it("renders with title and message", () => {
      render(<DivergenceWarning message={testMessage} variant="banner" />);

      expect(screen.getByText("Methodology Divergence Warning")).toBeInTheDocument();
      expect(screen.getByText(testMessage)).toBeInTheDocument();
    });

    it("includes link to methods page", () => {
      render(<DivergenceWarning message={testMessage} variant="banner" />);

      const link = screen.getByText("Learn about methodologies");
      expect(link).toBeInTheDocument();
      expect(link.closest("a")).toHaveAttribute("href", "/methods");
    });

    it("applies banner styling", () => {
      const { container } = render(
        <DivergenceWarning message={testMessage} variant="banner" />
      );

      const element = container.firstChild as HTMLElement;
      expect(element).toHaveClass("rounded-xl");
      expect(element).toHaveClass("border-amber-300");
    });
  });

  describe("default behavior", () => {
    it("renders inline variant by default", () => {
      render(<DivergenceWarning message={testMessage} />);

      expect(screen.getByText(testMessage)).toBeInTheDocument();
      const container = screen.getByText(testMessage).parentElement;
      expect(container).toHaveClass("bg-amber-50");
    });
  });

  describe("accessibility", () => {
    it("has sufficient color contrast", () => {
      render(<DivergenceWarning message={testMessage} variant="banner" />);

      // Check that the message text has good contrast
      const messageText = screen.getByText(testMessage);
      expect(messageText).toHaveClass("text-amber-800");
    });

    it("includes visual icon for non-text indicator", () => {
      const { container } = render(
        <DivergenceWarning message={testMessage} />
      );

      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });
  });
});
