import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { DataExport } from "@/components/DataExport";

describe("DataExport", () => {
  // Store original window.location
  const originalLocation = window.location;

  beforeEach(() => {
    // Mock window.location.href
    delete (window as any).location;
    window.location = { ...originalLocation, href: "" } as Location;
  });

  afterEach(() => {
    // Restore original window.location
    window.location = originalLocation;
  });

  it("renders with default state", () => {
    render(<DataExport />);

    expect(
      screen.getByRole("heading", { name: "Download Data" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Export wait time data with full methodology tags/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Download Data/i }),
    ).toBeInTheDocument();
  });

  it("displays citation information", () => {
    render(<DataExport />);

    expect(screen.getByText("Suggested Citation:")).toBeInTheDocument();
    expect(
      screen.getByText(/Wait Time Canada.*2026.*Canadian ER Wait Time Data/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/License: CC-BY-4.0/i)).toBeInTheDocument();
  });

  describe("province filter", () => {
    it('starts with "All Provinces" selected', () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Province") as HTMLSelectElement;
      expect(select.value).toBe("");
    });

    it("allows selecting specific province", () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Province") as HTMLSelectElement;
      fireEvent.change(select, { target: { value: "ON" } });

      expect(select.value).toBe("ON");
    });

    it("has Ontario, Quebec, and Alberta options", () => {
      render(<DataExport />);

      const options = screen.getAllByRole("option");
      const labels = options.map((opt) => opt.textContent);

      expect(labels).toContain("Ontario");
      expect(labels).toContain("Quebec");
      expect(labels).toContain("Alberta");
    });
  });

  describe("date range filter", () => {
    it('starts with "Last 7 Days" selected', () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Date Range") as HTMLSelectElement;
      expect(select.value).toBe("7d");
    });

    it("allows selecting different date ranges", () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Date Range") as HTMLSelectElement;
      fireEvent.change(select, { target: { value: "30d" } });

      expect(select.value).toBe("30d");
    });

    it("has all date range options including extended ranges", () => {
      render(<DataExport />);

      const options = screen.getAllByRole("option");
      const labels = options.map((opt) => opt.textContent);

      expect(labels).toContain("Last 24 Hours");
      expect(labels).toContain("Last 7 Days");
      expect(labels).toContain("Last 30 Days");
      expect(labels).toContain("Last 90 Days");
      expect(labels).toContain("Last 6 Months");
      expect(labels).toContain("Last Year");
      expect(labels).toContain("All Data");
    });
  });

  describe("granularity selector", () => {
    it("renders the granularity selector", () => {
      render(<DataExport />);

      expect(screen.getByLabelText("Data Granularity")).toBeInTheDocument();
    });

    it("starts with raw granularity selected", () => {
      render(<DataExport />);

      const select = screen.getByLabelText(
        "Data Granularity",
      ) as HTMLSelectElement;
      expect(select.value).toBe("raw");
    });

    it("has all granularity options", () => {
      render(<DataExport />);

      const options = screen.getAllByRole("option");
      const labels = options.map((opt) => opt.textContent);

      expect(labels).toContain("Raw Measurements");
      expect(labels).toContain("Hourly Averages");
      expect(labels).toContain("Daily Averages");
      expect(labels).toContain("Weekly Averages");
      expect(labels).toContain("Monthly Averages");
    });

    it("shows raw data help text by default", () => {
      render(<DataExport />);

      expect(
        screen.getByText(/Raw data is available for the last 30 days/i),
      ).toBeInTheDocument();
    });

    it("shows aggregated help text when aggregate selected", () => {
      render(<DataExport />);

      const select = screen.getByLabelText(
        "Data Granularity",
      ) as HTMLSelectElement;
      fireEvent.change(select, { target: { value: "daily" } });

      expect(
        screen.getByText(/Aggregated data includes mean, median, P90/i),
      ).toBeInTheDocument();
    });

    it("granularity is passed as query parameter in download URL", () => {
      render(<DataExport />);

      const granularitySelect = screen.getByLabelText(
        "Data Granularity",
      ) as HTMLSelectElement;
      fireEvent.change(granularitySelect, { target: { value: "weekly" } });

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      expect(window.location.href).toContain("granularity=weekly");
    });
  });

  describe("raw data warning", () => {
    it("shows warning when raw data selected with >30 day range", () => {
      render(<DataExport />);

      const dateRangeSelect = screen.getByLabelText("Date Range");
      fireEvent.change(dateRangeSelect, { target: { value: "90d" } });

      expect(
        screen.getByText(/Raw measurements are retained for 30 days/i),
      ).toBeInTheDocument();
    });

    it("does not show warning for raw data within 30 days", () => {
      render(<DataExport />);

      // Default is 7d + raw, no warning
      expect(
        screen.queryByText(/Raw measurements are retained for 30 days/i),
      ).not.toBeInTheDocument();
    });

    it("does not show warning for aggregated data with long range", () => {
      render(<DataExport />);

      const granularitySelect = screen.getByLabelText("Data Granularity");
      fireEvent.change(granularitySelect, { target: { value: "daily" } });

      const dateRangeSelect = screen.getByLabelText("Date Range");
      fireEvent.change(dateRangeSelect, { target: { value: "90d" } });

      expect(
        screen.queryByText(/Raw measurements are retained for 30 days/i),
      ).not.toBeInTheDocument();
    });
  });

  describe("format toggle", () => {
    it("starts with CSV format selected", () => {
      render(<DataExport />);

      const csvButton = screen.getByRole("button", { name: /CSV/i });
      expect(csvButton).toHaveClass("bg-primary/10");
    });

    it("allows switching to JSON format", () => {
      render(<DataExport />);

      const jsonButton = screen.getByRole("button", { name: /JSON/i });
      fireEvent.click(jsonButton);

      expect(jsonButton).toHaveClass("bg-primary/10");
    });

    it("highlights only selected format", () => {
      render(<DataExport />);

      const csvButton = screen.getByRole("button", { name: /CSV/i });
      const jsonButton = screen.getByRole("button", { name: /JSON/i });

      // Initially CSV is selected
      expect(csvButton).toHaveClass("bg-primary/10");
      expect(jsonButton).not.toHaveClass("bg-primary/10");

      // Click JSON
      fireEvent.click(jsonButton);
      expect(jsonButton).toHaveClass("bg-primary/10");
      expect(csvButton).not.toHaveClass("bg-primary/10");
    });
  });

  describe("download functionality", () => {
    it("triggers download with correct URL for default options", () => {
      render(<DataExport />);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      // Should construct URL with format=csv, granularity=raw, and start_date for 7d range
      expect(window.location.href).toContain("/api/export");
      expect(window.location.href).toContain("format=csv");
      expect(window.location.href).toContain("granularity=raw");
      expect(window.location.href).toContain("start_date=");
    });

    it("includes province parameter when selected", () => {
      render(<DataExport />);

      const provinceSelect = screen.getByLabelText("Province");
      fireEvent.change(provinceSelect, { target: { value: "ON" } });

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      expect(window.location.href).toContain("province=ON");
    });

    it("uses JSON format when selected", () => {
      render(<DataExport />);

      const jsonButton = screen.getByRole("button", { name: /JSON/i });
      fireEvent.click(jsonButton);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      expect(window.location.href).toContain("format=json");
    });

    it('does not include start_date for "All Data" range', () => {
      render(<DataExport />);

      const dateRangeSelect = screen.getByLabelText("Date Range");
      fireEvent.change(dateRangeSelect, { target: { value: "all" } });

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      expect(window.location.href).not.toContain("start_date=");
    });

    it("shows loading state during download", () => {
      vi.useFakeTimers();
      render(<DataExport />);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      // Loading state should appear immediately (synchronous)
      expect(
        screen.getByRole("button", { name: /Preparing/i }),
      ).toBeInTheDocument();
      expect(downloadButton).toBeDisabled();

      // Advance all timers to complete the loading timeout
      act(() => {
        vi.runAllTimers();
      });

      // Button should now be back to normal state
      expect(
        screen.getByRole("button", { name: /Download Data/i }),
      ).toBeInTheDocument();
      expect(downloadButton).not.toBeDisabled();

      vi.useRealTimers();
    });
  });

  describe("accessibility", () => {
    it("has proper labels for form controls", () => {
      render(<DataExport />);

      expect(screen.getByLabelText("Province")).toBeInTheDocument();
      expect(screen.getByLabelText("Date Range")).toBeInTheDocument();
      expect(screen.getByLabelText("Data Granularity")).toBeInTheDocument();
    });

    it("download button is keyboard accessible", () => {
      render(<DataExport />);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      expect(downloadButton).toBeEnabled();
      expect(downloadButton.tagName).toBe("BUTTON");
    });

    it("format toggle buttons are keyboard accessible", () => {
      render(<DataExport />);

      const csvButton = screen.getByRole("button", { name: /CSV/i });
      const jsonButton = screen.getByRole("button", { name: /JSON/i });

      expect(csvButton).toBeEnabled();
      expect(jsonButton).toBeEnabled();
    });
  });
});
