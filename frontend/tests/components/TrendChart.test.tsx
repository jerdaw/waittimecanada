import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { TrendChart } from "../../components/TrendChart";

// Mock Recharts
// Recharts uses ResizeObserver which needs to be mocked or we can mock the components
vi.mock("recharts", () => {
  const PropMonitor = ({ children, data }: any) => (
    <div data-testid="recharts-mock" data-data={JSON.stringify(data)}>
      {children}
    </div>
  );
  return {
    ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
    LineChart: PropMonitor,
    Line: () => <div />,
    XAxis: () => <div />,
    YAxis: () => <div />,
    Tooltip: () => <div />,
    CartesianGrid: () => <div />,
  };
});

describe("TrendChart Component", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("renders loading state initially", () => {
    // @ts-ignore
    global.fetch.mockReturnValue(new Promise(() => {}));
    render(<TrendChart hospitalId="test-id" />);
    // The spinner might not have text, we check for layout or class
    // In our component, loading is a div with animate-spin
    // Let's modify component to have test id or text for easier testing
    // Or just check if chart is NOT there
    expect(screen.queryByTestId("recharts-mock")).not.toBeInTheDocument();
  });

  it("renders chart when data loads", async () => {
    const mockResponse = {
      period: "24h",
      dataPoints: [{ timestamp: "2023-01-01", waitTime: 60 }],
      aggregation: "hourly"
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse)
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByTestId("recharts-mock")).toBeInTheDocument();
    });

    // Check header
    expect(screen.getByText("Wait Time Trends")).toBeInTheDocument();
  });

  it("displays error message on failure", async () => {
    // @ts-ignore
    global.fetch.mockRejectedValue(new Error("Network error"));

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load trends")).toBeInTheDocument();
    });
  });

  it("allows switching time periods", async () => {
    const mockResponse = {
      period: "24h",
      dataPoints: [],
      aggregation: "hourly"
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse)
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText("24h")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("7d"));
    
    // API should be called with new period
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("period=7d"));
  });
});
