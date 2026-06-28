import {
  act,
  render,
  screen,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
  beforeEach,
  afterEach,
  type Mock,
} from "vitest";
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

function mockFetchResponse(body: unknown) {
  return {
    json: () => Promise.resolve(body),
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });

  return { promise, resolve };
}

describe("TrendChart Component", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
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
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    // @ts-ignore
    global.fetch.mockRejectedValue(new Error("Network error"));

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load trends")).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(errorSpy).toHaveBeenCalledWith(new Error("Network error"));
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

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("period=7d"),
      );
    });
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
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("period=90d"),
      );
    });

    fireEvent.click(screen.getByText("1y"));
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("period=1y"),
      );
    });
  });

  it("ignores stale period responses after a newer period resolves", async () => {
    const initialResponse = {
      period: "24h",
      dataPoints: [{ timestamp: "2023-01-01", waitTime: 10 }],
      aggregation: "hourly",
      dataSource: "raw",
    };
    const slow7dResponse = {
      period: "7d",
      dataPoints: [{ timestamp: "2023-02-01", waitTime: 70 }],
      aggregation: "daily",
      dataSource: "raw",
    };
    const fast90dResponse = {
      period: "90d",
      dataPoints: [
        {
          timestamp: "2023-03-01",
          waitTime: 90,
          minWaitTime: 80,
          maxWaitTime: 100,
        },
      ],
      aggregation: "daily",
      dataSource: "aggregated",
    };
    const slow7d = deferred<ReturnType<typeof mockFetchResponse>>();
    const fast90d = deferred<ReturnType<typeof mockFetchResponse>>();
    const fetchMock = global.fetch as Mock;

    fetchMock
      .mockResolvedValueOnce(mockFetchResponse(initialResponse))
      .mockReturnValueOnce(slow7d.promise)
      .mockReturnValueOnce(fast90d.promise);

    render(<TrendChart hospitalId="test-id" />);

    await waitFor(() => {
      expect(screen.getByTestId("recharts-mock")).toHaveAttribute(
        "data-data",
        JSON.stringify(initialResponse.dataPoints),
      );
    });

    fireEvent.click(screen.getByText("7d"));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("period=7d"),
      );
    });

    fireEvent.click(screen.getByText("90d"));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("period=90d"),
      );
    });

    await act(async () => {
      fast90d.resolve(mockFetchResponse(fast90dResponse));
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText("Aggregated")).toBeInTheDocument();
    expect(screen.getByTestId("recharts-mock")).toHaveAttribute(
      "data-data",
      JSON.stringify(fast90dResponse.dataPoints),
    );

    await act(async () => {
      slow7d.resolve(mockFetchResponse(slow7dResponse));
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText("Aggregated")).toBeInTheDocument();
    expect(screen.getByTestId("recharts-mock")).toHaveAttribute(
      "data-data",
      JSON.stringify(fast90dResponse.dataPoints),
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
