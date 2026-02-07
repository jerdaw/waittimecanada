import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DataQualityCard } from "../../components/DataQualityCard";

const makeSource = (overrides = {}) => ({
  source_id: "ontario-er",
  source_name: "Ontario Emergency Rooms",
  province: "ON",
  last_24h_success_rate: 0.97,
  last_7d_success_rate: 0.95,
  hospitals_reporting: 12,
  total_hospitals: 15,
  last_heartbeat_age_minutes: 5,
  scraper_status: "healthy",
  ...overrides,
});

describe("DataQualityCard", () => {
  it("renders source name and province", () => {
    render(<DataQualityCard source={makeSource()} />);
    expect(screen.getByText("Ontario Emergency Rooms")).toBeInTheDocument();
    expect(screen.getByText("(ON)")).toBeInTheDocument();
  });

  it("shows success rate with green color for healthy", () => {
    render(<DataQualityCard source={makeSource({ last_24h_success_rate: 0.97 })} />);
    expect(screen.getByText("97.0%")).toBeInTheDocument();
  });

  it("shows success rate for degraded performance", () => {
    render(<DataQualityCard source={makeSource({ last_24h_success_rate: 0.85 })} />);
    expect(screen.getByText("85.0%")).toBeInTheDocument();
  });

  it("shows success rate for critical performance", () => {
    render(<DataQualityCard source={makeSource({ last_24h_success_rate: 0.5 })} />);
    expect(screen.getByText("50.0%")).toBeInTheDocument();
  });

  it("displays hospital count", () => {
    render(<DataQualityCard source={makeSource()} />);
    expect(screen.getByText("12/15 hospitals reporting")).toBeInTheDocument();
  });

  it("shows heartbeat age", () => {
    render(<DataQualityCard source={makeSource({ last_heartbeat_age_minutes: 5 })} />);
    expect(screen.getByText("5m ago")).toBeInTheDocument();
  });

  it("shows 'Never' when heartbeat is null", () => {
    render(<DataQualityCard source={makeSource({ last_heartbeat_age_minutes: null })} />);
    expect(screen.getByText("Never")).toBeInTheDocument();
  });

  it("shows both 24h and 7d rates", () => {
    render(<DataQualityCard source={makeSource()} />);
    expect(screen.getByText("24h Rate")).toBeInTheDocument();
    expect(screen.getByText("7d Rate")).toBeInTheDocument();
  });
});
