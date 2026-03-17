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
    ComposedChart: PropMonitor,
    Line: () => <div />,
    Area: () => <div />,
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
    expect(screen.queryByTestId("recharts-mock")).not.toBeInTheDocument();
  });

  it("renders chart when data loads", async () => {
    const mockResponse = {
      period: "24h",
      dataPoints: [{ timestamp: "2023-01-01", waitTime: 60 }],
      aggregation: "hourly",
      dataSource: "raw",
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
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

    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("renders all six period buttons", async () => {
    const mockResponse = {
      period: "24h",
      dataPoints: [],
      aggregation: "hourly",
      dataSource: "raw",
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText("24h")).toBeInTheDocument();
    });

    expect(screen.getByText("24h")).toBeInTheDocument();
    expect(screen.getByText("7d")).toBeInTheDocument();
    expect(screen.getByText("30d")).toBeInTheDocument();
    expect(screen.getByText("90d")).toBeInTheDocument();
    expect(screen.getByText("6m")).toBeInTheDocument();
    expect(screen.getByText("1y")).toBeInTheDocument();
  });

  it("allows switching time periods", async () => {
    const mockResponse = {
      period: "24h",
      dataPoints: [],
      aggregation: "hourly",
      dataSource: "raw",
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText("24h")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("7d"));

    // API should be called with new period
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("period=7d"),
    );
  });

  it("allows switching to long-range periods", async () => {
    const mockResponse = {
      period: "24h",
      dataPoints: [],
      aggregation: "hourly",
      dataSource: "raw",
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText("90d")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("90d"));
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("period=90d"),
    );

    fireEvent.click(screen.getByText("1y"));
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("period=1y"),
    );
  });

  it("shows aggregated badge when viewing aggregated data", async () => {
    const mockResponse = {
      period: "90d",
      dataPoints: [
        {
          timestamp: "2023-01-01",
          waitTime: 60,
          minWaitTime: 30,
          maxWaitTime: 120,
          sampleCount: 24,
        },
      ],
      aggregation: "daily",
      dataSource: "aggregated",
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText("Aggregated")).toBeInTheDocument();
    });
  });

  it("does not show aggregated badge for raw data", async () => {
    const mockResponse = {
      period: "24h",
      dataPoints: [{ timestamp: "2023-01-01", waitTime: 60 }],
      aggregation: "hourly",
      dataSource: "raw",
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByTestId("recharts-mock")).toBeInTheDocument();
    });

    expect(screen.queryByText("Aggregated")).not.toBeInTheDocument();
  });

  it("shows no data message for empty results", async () => {
    const mockResponse = {
      period: "1y",
      dataPoints: [],
      aggregation: "monthly",
      dataSource: "aggregated",
    };

    // @ts-ignore
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve(mockResponse),
    });

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(
        screen.getByText("No historical data available"),
      ).toBeInTheDocument();
    });
  });
});
