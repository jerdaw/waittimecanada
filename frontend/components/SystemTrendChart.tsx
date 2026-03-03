"use client";

import { useEffect, useMemo, useState } from "react";
import { clsx } from "clsx";
import {
  Area,
  ComposedChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type TrendDirection = "improving" | "stable" | "worsening";
type PeriodType = "weekly" | "monthly";
type Lookback = "3m" | "6m" | "1y";

interface TrendPoint {
  period_start: string;
  period_end: string;
  province_mean: number;
  province_median: number;
  province_p90: number;
  hospitals_reporting: number;
  total_measurements: number;
  range_min: number;
  range_max: number;
}

interface TrendsApiResponse {
  success: boolean;
  data?: {
    province: string;
    period: PeriodType;
    lookback: Lookback;
    generated_at: string;
    data_points: TrendPoint[];
    trend_summary: {
      direction: TrendDirection;
      change_percent: number;
      start_mean: number | null;
      end_mean: number | null;
      narrative: string;
    };
  };
  error?: string;
}

interface SystemTrendChartProps {
  province?: string;
  metricFamily?: string;
  className?: string;
}

const LOOKBACK_OPTIONS: Array<{ value: Lookback; label: string }> = [
  { value: "3m", label: "3m" },
  { value: "6m", label: "6m" },
  { value: "1y", label: "1y" },
];

const PERIOD_OPTIONS: Array<{ value: PeriodType; label: string }> = [
  { value: "monthly", label: "Monthly" },
  { value: "weekly", label: "Weekly" },
];

function provinceLabel(code: string): string {
  const labels: Record<string, string> = {
    ON: "Ontario",
    QC: "Quebec",
    AB: "Alberta",
    BC: "British Columbia",
  };
  return labels[code] ?? code;
}

function directionClasses(direction: TrendDirection): string {
  if (direction === "improving") {
    return "bg-emerald-50 text-emerald-700 border-emerald-200";
  }
  if (direction === "worsening") {
    return "bg-red-50 text-red-700 border-red-200";
  }
  return "bg-slate-50 text-slate-700 border-slate-200";
}

function directionPrefix(direction: TrendDirection): string {
  if (direction === "improving") return "↓";
  if (direction === "worsening") return "↑";
  return "→";
}

function formatPeriodLabel(point: TrendPoint, period: PeriodType): string {
  const start = new Date(point.period_start);
  if (period === "weekly") {
    const month = start.toLocaleString("en-CA", {
      month: "short",
      timeZone: "UTC",
    });
    return `${month} ${start.getUTCDate()}`;
  }

  const month = start.toLocaleString("en-CA", {
    month: "short",
    timeZone: "UTC",
  });
  return `${month} '${String(start.getUTCFullYear()).slice(2)}`;
}

export function SystemTrendChart({
  province = "ON",
  metricFamily = "TIME_TO_PROVIDER",
  className = "rounded-xl border border-border/50 bg-card p-4",
}: SystemTrendChartProps) {
  const [period, setPeriod] = useState<PeriodType>("monthly");
  const [lookback, setLookback] = useState<Lookback>("6m");
  const [payload, setPayload] = useState<TrendsApiResponse["data"] | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const query = new URLSearchParams({
          province,
          period,
          lookback,
          metric_family: metricFamily,
        });

        const response = await fetch(
          `/api/analytics/trends?${query.toString()}`,
          {
            signal: controller.signal,
          },
        );
        const json = (await response.json()) as TrendsApiResponse;

        if (!mounted) return;

        if (!response.ok || !json.success || !json.data) {
          setPayload(null);
          setError("Unable to load system trends");
          setLoading(false);
          return;
        }

        setPayload(json.data);
        setLoading(false);
      } catch (err) {
        if (!mounted || (err as Error).name === "AbortError") return;
        setPayload(null);
        setError("Unable to load system trends");
        setLoading(false);
      }
    }

    load();

    return () => {
      mounted = false;
      controller.abort();
    };
  }, [province, period, lookback, metricFamily]);

  const chartData = useMemo(() => {
    if (!payload) return [];

    return payload.data_points.map((point) => ({
      ...point,
      label: formatPeriodLabel(point, payload.period),
      range_span: Number((point.range_max - point.range_min).toFixed(1)),
    }));
  }, [payload]);

  const trendSummary = payload?.trend_summary;
  const hasData = chartData.length > 0;

  return (
    <section className={className}>
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            {metricFamily === "STRETCHER_OCCUPANCY"
              ? "Occupancy Trend"
              : "Wait Time Trend"}
          </h2>
          <p className="text-xs text-muted-foreground">
            {metricFamily === "STRETCHER_OCCUPANCY"
              ? `Province-wide emergency stretcher occupancy trend for ${provinceLabel(province)}`
              : `Province-wide emergency wait trend for ${provinceLabel(province)}`}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex rounded-lg border border-border/60 bg-muted/20 p-1">
            {PERIOD_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setPeriod(option.value)}
                className={clsx(
                  "px-2.5 py-1 text-xs rounded-md font-medium transition-colors",
                  period === option.value
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="inline-flex rounded-lg border border-border/60 bg-muted/20 p-1">
            {LOOKBACK_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setLookback(option.value)}
                className={clsx(
                  "px-2.5 py-1 text-xs rounded-md font-medium transition-colors",
                  lookback === option.value
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {trendSummary && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span
            className={clsx(
              "text-xs font-semibold px-2.5 py-1 rounded-full border",
              directionClasses(trendSummary.direction),
            )}
          >
            {directionPrefix(trendSummary.direction)}{" "}
            {Math.abs(trendSummary.change_percent).toFixed(1)}%
          </span>
          <span className="text-xs text-muted-foreground">
            {provinceLabel(province)}{" "}
            {metricFamily === "STRETCHER_OCCUPANCY"
              ? "ER occupancy"
              : "ER waits"}{" "}
            over {lookback}
          </span>
        </div>
      )}

      <div className="h-[280px] w-full">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center text-sm text-red-600">
            {error}
          </div>
        ) : !hasData ? (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            Not enough province trend data yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="var(--border)"
              />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={40}
              />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="range_min"
                stackId="band"
                stroke="none"
                fill="transparent"
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="range_span"
                stackId="band"
                stroke="none"
                fill="var(--primary)"
                fillOpacity={0.12}
                isAnimationActive={false}
                name="Range"
              />
              <Line
                type="monotone"
                dataKey="province_mean"
                stroke="var(--primary)"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 4 }}
                name="Province mean"
              />
              <Line
                type="monotone"
                dataKey="province_p90"
                stroke="var(--destructive)"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
                name="P90"
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      {trendSummary && !loading && !error && (
        <p className="mt-3 text-sm text-muted-foreground">
          {trendSummary.narrative}
        </p>
      )}
    </section>
  );
}
