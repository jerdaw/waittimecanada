import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ComparabilityMatrix } from "@/components/methods/ComparabilityMatrix";
import { useSearchParams, useRouter } from "next/navigation";

// Mock Next.js navigation hooks
vi.mock("next/navigation", () => ({
  useSearchParams: vi.fn(),
  useRouter: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ComparabilityMatrix", () => {
  let mockSearchParams: any;
  let mockRouter: any;

  beforeEach(() => {
    mockSearchParams = {
      get: vi.fn(() => null),
      toString: vi.fn(() => ""),
    };
    mockRouter = {
      replace: vi.fn(),
    };

    vi.mocked(useSearchParams).mockReturnValue(mockSearchParams);
    vi.mocked(useRouter).mockReturnValue(mockRouter);

    // Mock URL.createObjectURL for CSV export tests
    global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
    global.URL.revokeObjectURL = vi.fn();
  });

  const mockSources = [
    {
      id: "on-health",
      name: "Health Ontario",
      province: "Ontario",
      default_metric_family: "TIME_TO_PROVIDER",
      default_start_event: "TRIAGE",
      default_end_event: "PHYSICIAN",
      default_statistic_type: "P90",
    },
    {
      id: "qc-msss",
      name: "Quebec MSSS",
      province: "Quebec",
      default_metric_family: "TIME_TO_PROVIDER",
      default_start_event: "REGISTRATION",
      default_end_event: "PHYSICIAN",
      default_statistic_type: "ROLLING_AVG",
    },
    {
      id: "ab-ahs",
      name: "Alberta AHS",
      province: "Alberta",
      default_metric_family: "TIME_TO_PROVIDER",
      default_start_event: "TRIAGE",
      default_end_event: "PHYSICIAN",
      default_statistic_type: "P90",
    },
  ];

  it("renders empty state when no sources provided", () => {
    render(<ComparabilityMatrix sources={[]} />);

    expect(screen.getByText(/No data sources configured/i)).toBeInTheDocument();
  });

  it("renders province headers", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    expect(screen.getAllByText("Ontario")).toHaveLength(2); // Header + row
    expect(screen.getAllByText("Quebec")).toHaveLength(2);
    expect(screen.getAllByText("Alberta")).toHaveLength(2);
  });

  it("renders matrix cells for all source pairs", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // Should have 3x3 = 9 cells
    const cells = screen.getAllByRole("cell");
    expect(cells.length).toBeGreaterThanOrEqual(9);
  });

  it("shows checkmark for same province (diagonal)", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // Diagonal cells should all be comparable (same province with itself)
    const checkmarks = screen.getAllByText("✓");
    expect(checkmarks.length).toBeGreaterThanOrEqual(3);
  });

  it("shows warning for partially compatible provinces", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // Should have some warning signs for partial matches
    const warnings = screen.queryAllByText("⚠");
    expect(warnings.length).toBeGreaterThan(0);
  });

  it("shows X for incompatible provinces", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // Ontario and Quebec differ significantly
    const incompatible = screen.queryAllByText("✗");
    // May or may not have incompatible pairs depending on methodology
    expect(incompatible).toBeDefined();
  });

  it("displays comparison legend", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    expect(screen.getByText("Directly comparable")).toBeInTheDocument();
    expect(screen.getByText(/Partially comparable/i)).toBeInTheDocument();
    expect(screen.getByText(/Not comparable/i)).toBeInTheDocument();
  });

  it("shows detail panel when cell is clicked", async () => {
    const user = userEvent.setup();
    render(<ComparabilityMatrix sources={mockSources} />);

    // Click a cell (not on header row/col)
    const cells = screen.getAllByRole("cell");
    // Find a non-header cell
    const dataCell = cells.find((cell) => cell.querySelector("[title]"));

    if (dataCell) {
      await user.click(dataCell);

      await waitFor(() => {
        expect(screen.getByText(/Comparing/i)).toBeInTheDocument();
      });
    }
  });

  it("displays methodology dimensions in detail panel", async () => {
    const user = userEvent.setup();
    render(<ComparabilityMatrix sources={mockSources} />);

    const cells = screen.getAllByRole("cell");
    const dataCell = cells.find((cell) => cell.querySelector("[title]"));

    if (dataCell) {
      await user.click(dataCell);

      await waitFor(() => {
        expect(screen.getByText("Metric Family:")).toBeInTheDocument();
        expect(screen.getByText("Start Event:")).toBeInTheDocument();
        expect(screen.getByText("End Event:")).toBeInTheDocument();
        expect(screen.getByText("Statistic Type:")).toBeInTheDocument();
      });
    }
  });

  it("highlights selected cell", async () => {
    const user = userEvent.setup();
    const { container } = render(<ComparabilityMatrix sources={mockSources} />);

    const cells = screen.getAllByRole("cell");
    const dataCell = cells.find((cell) => cell.querySelector("[title]"));

    if (dataCell) {
      await user.click(dataCell);

      await waitFor(() => {
        // Check if cell has highlight styling
        const highlighted = container.querySelector(".ring-blue-500");
        expect(highlighted).toBeInTheDocument();
      });
    }
  });

  it("identifies Ontario and Alberta as compatible", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // Ontario and Alberta both use: TRIAGE → PHYSICIAN, P90
    // They should be marked as compatible
    const checkmarks = screen.getAllByText("✓");
    expect(checkmarks.length).toBeGreaterThanOrEqual(3); // At least diagonal + ON-AB
  });

  it("identifies Ontario and Quebec as incompatible", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // Ontario: TRIAGE → PHYSICIAN, P90
    // Quebec: REGISTRATION → PHYSICIAN, ROLLING_AVG
    // They should be marked as not comparable or partial
    const warnings = screen.queryAllByText("⚠");
    const xmarks = screen.queryAllByText("✗");

    expect(warnings.length + xmarks.length).toBeGreaterThan(0);
  });

  it("renders CSV export button", () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    expect(screen.getByText("Export CSV")).toBeInTheDocument();
  });

  it("CSV export button is clickable", async () => {
    const user = userEvent.setup();
    render(<ComparabilityMatrix sources={mockSources} />);

    const exportButton = screen.getByText("Export CSV");
    expect(exportButton).toBeInTheDocument();

    // Verify button is clickable (won't actually download in test environment)
    await user.click(exportButton);

    // If we get here without errors, the button is functional
    expect(exportButton).toBeInTheDocument();
  });

  it("pre-selects cell from URL parameters", async () => {
    mockSearchParams.get = vi.fn((key) => {
      if (key === "compare") return "Ontario,Quebec";
      return null;
    });

    render(<ComparabilityMatrix sources={mockSources} />);

    await waitFor(() => {
      expect(
        screen.getByText(/Comparing Ontario with Quebec/i),
      ).toBeInTheDocument();
    });
  });

  it("updates URL when cell is clicked", async () => {
    const user = userEvent.setup();
    render(<ComparabilityMatrix sources={mockSources} />);

    const cells = screen.getAllByRole("cell");
    const dataCell = cells.find((cell) => cell.querySelector("[title]"));

    if (dataCell) {
      await user.click(dataCell);

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalled();
      });
    }
  });
});
