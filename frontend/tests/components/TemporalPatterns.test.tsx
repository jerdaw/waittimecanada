import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TemporalPatterns } from "@/components/TemporalPatterns";

vi.mock("recharts", () => {
  const Monitor = ({
    children,
    data,
  }: {
    children: React.ReactNode;
    data: unknown;
  }) => (
    <div data-testid="recharts-mock" data-data={JSON.stringify(data)}>
      {children}
    </div>
  );

  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div>{children}</div>
    ),
    BarChart: Monitor,
    LineChart: Monitor,
    CartesianGrid: () => <div />,
    XAxis: () => <div />,
    YAxis: () => <div />,
    Tooltip: () => <div />,
    Bar: () => <div />,
    Line: () => <div />,
  };
});

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("TemporalPatterns", () => {
  let fetchMock: ReturnType<
    typeof vi.fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>
  >;

  beforeEach(() => {
    fetchMock = vi.fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>();
    global.fetch = fetchMock;
  });

  it("renders hour-of-day chart and insight", async () => {
    const patterns = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      mean: hour === 14 ? 180 : hour === 4 ? 70 : 100,
      median: 95,
      sample_count: 10,
    }));

    fetchMock.mockResolvedValue(
      jsonResponse({
        success: true,
        data: {
          hospital_id: "ca-on-test",
          hospital_name: "Test Hospital",
          pattern_type: "hour_of_day",
          sample_count: 240,
          patterns,
          insights: {
            peak_hour: 14,
            quietest_hour: 4,
            peak_mean: 180,
            quietest_mean: 70,
            peak_vs_quiet_ratio: 2.57,
          },
        },
      }),
    );

    render(<TemporalPatterns hospitalId="ca-on-test" />);

    await waitFor(() => {
      expect(screen.getByTestId("recharts-mock")).toBeInTheDocument();
    });

    expect(screen.getByText("Temporal Patterns")).toBeInTheDocument();
    expect(screen.getByText(/Peak at 14:00/)).toBeInTheDocument();
  });

  it("switches tabs and fetches day-of-week", async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: {
            hospital_id: "ca-on-test",
            hospital_name: "Test Hospital",
            pattern_type: "hour_of_day",
            sample_count: 24,
            patterns: Array.from({ length: 24 }, (_, hour) => ({
              hour,
              mean: 100,
              median: 95,
              sample_count: 5,
            })),
            insights: {
              peak_hour: 14,
              quietest_hour: 4,
              peak_mean: 180,
              quietest_mean: 70,
              peak_vs_quiet_ratio: 2.57,
            },
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: {
            hospital_id: "ca-on-test",
            hospital_name: "Test Hospital",
            pattern_type: "day_of_week",
            sample_count: 70,
            patterns: [
              {
                day: "Monday",
                day_index: 0,
                mean: 100,
                median: 95,
                sample_count: 10,
              },
              {
                day: "Tuesday",
                day_index: 1,
                mean: 110,
                median: 100,
                sample_count: 10,
              },
              {
                day: "Wednesday",
                day_index: 2,
                mean: 95,
                median: 90,
                sample_count: 10,
              },
              {
                day: "Thursday",
                day_index: 3,
                mean: 105,
                median: 100,
                sample_count: 10,
              },
              {
                day: "Friday",
                day_index: 4,
                mean: 115,
                median: 110,
                sample_count: 10,
              },
              {
                day: "Saturday",
                day_index: 5,
                mean: 125,
                median: 120,
                sample_count: 10,
              },
              {
                day: "Sunday",
                day_index: 6,
                mean: 130,
                median: 125,
                sample_count: 10,
              },
            ],
            insights: {
              worst_day: "Sunday",
              best_day: "Wednesday",
              weekend_vs_weekday_ratio: 1.18,
            },
          },
        }),
      );

    render(<TemporalPatterns hospitalId="ca-on-test" />);

    await waitFor(() => {
      expect(screen.getByText("Hour")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Day"));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("type=day_of_week"),
        expect.any(Object),
      );
    });

    expect(screen.getByText(/Weekend\/weekday ratio/)).toBeInTheDocument();
  });

  it("shows empty state when no data", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        success: true,
        data: {
          hospital_id: "ca-on-test",
          hospital_name: "Test Hospital",
          pattern_type: "hour_of_day",
          sample_count: 0,
          patterns: Array.from({ length: 24 }, (_, hour) => ({
            hour,
            mean: null,
            median: null,
            sample_count: 0,
          })),
          insights: {
            peak_hour: null,
            quietest_hour: null,
            peak_mean: null,
            quietest_mean: null,
            peak_vs_quiet_ratio: null,
          },
        },
      }),
    );

    render(<TemporalPatterns hospitalId="ca-on-test" />);

    await waitFor(() => {
      expect(
        screen.getByText("Not enough pattern data yet"),
      ).toBeInTheDocument();
    });
  });
});
