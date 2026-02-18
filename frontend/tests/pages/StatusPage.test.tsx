import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import StatusPage from "../../app/[locale]/status/page";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock Header component
vi.mock("../../components/Header", () => ({
  Header: () => <header data-testid="header">Header</header>,
}));

const makeSource = (overrides = {}) => ({
  source_id: "ca-on-oh",
  source_name: "Ontario Health",
  province: "ON",
  uptime_24h: 0.97,
  uptime_7d: 0.95,
  uptime_30d: 0.93,
  total_hospitals: 15,
  last_heartbeat_age_minutes: 5,
  scraper_status: "healthy",
  last_run: "2026-02-18T12:00:00Z",
  ...overrides,
});

const makeStatus = (overrides = {}) => ({
  overall_status: "healthy" as const,
  system_uptime_24h: 0.97,
  sources: [makeSource()],
  drift_events: [],
  generated_at: "2026-02-18T12:00:00Z",
  ...overrides,
});

describe("StatusPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows loading spinner initially", () => {
    global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch;
    render(<StatusPage />);
    expect(document.querySelector(".animate-spin")).toBeTruthy();
  });

  it("renders overall status after load", async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: () => Promise.resolve(makeStatus()),
    }) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      expect(screen.getByTestId("overall-status")).toBeInTheDocument();
    });
    expect(screen.getByText("Overall Health")).toBeInTheDocument();
  });

  it("shows healthy status badge", async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: () => Promise.resolve(makeStatus({ overall_status: "healthy" })),
    }) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      // "Healthy" appears in both the overall section and the source card
      const badges = screen.getAllByText("Healthy");
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows degraded status badge", async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: () =>
        Promise.resolve(
          makeStatus({
            overall_status: "degraded",
            system_uptime_24h: 0.85,
            sources: [makeSource({ uptime_24h: 0.85 })],
          }),
        ),
    }) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      const badges = screen.getAllByText("Degraded");
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });


  it("renders source cards for each province", async () => {
    const sources = [
      makeSource({ source_id: "ca-on-oh", source_name: "Ontario Health", province: "ON" }),
      makeSource({ source_id: "ca-qc-msss", source_name: "Quebec MSSS", province: "QC" }),
    ];
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: () => Promise.resolve(makeStatus({ sources })),
    }) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      expect(screen.getAllByTestId("source-card")).toHaveLength(2);
    });
    expect(screen.getByText("Ontario Health")).toBeInTheDocument();
    expect(screen.getByText("Quebec MSSS")).toBeInTheDocument();
  });

  it("shows 'no drift events' message when list is empty", async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: () => Promise.resolve(makeStatus({ drift_events: [] })),
    }) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      expect(
        screen.getByText(/No drift events detected/i),
      ).toBeInTheDocument();
    });
  });

  it("renders drift events when present", async () => {
    const driftEvents = [
      {
        source_id: "ca-on-oh",
        previous_period_start: "2026-02-04",
        current_period_start: "2026-02-11",
        previous_mean: 100,
        current_mean: 130,
        shift_percent: 30.0,
        hospitals_analyzed: 6,
        explanation: "Province-wide mean increased by 30.0% across 6 hospitals.",
        detected_at: "2026-02-18T08:00:00Z",
      },
    ];
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: () => Promise.resolve(makeStatus({ drift_events: driftEvents })),
    }) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      expect(screen.getByText("ca-on-oh")).toBeInTheDocument();
    });
    expect(
      screen.getByText(/Province-wide mean increased by 30.0%/),
    ).toBeInTheDocument();
  });

  it("shows error message on fetch failure", async () => {
    global.fetch = vi.fn().mockRejectedValueOnce(
      new Error("Network error"),
    ) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load system status/i)).toBeInTheDocument();
    });
  });

  it("shows hospital count in summary", async () => {
    const sources = [
      makeSource({ total_hospitals: 15 }),
      makeSource({ source_id: "ca-qc-msss", total_hospitals: 10 }),
    ];
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: () => Promise.resolve(makeStatus({ sources })),
    }) as unknown as typeof fetch;

    render(<StatusPage />);

    await waitFor(() => {
      // 15 + 10 = 25 total hospitals
      expect(screen.getByText("25")).toBeInTheDocument();
    });
  });
});
