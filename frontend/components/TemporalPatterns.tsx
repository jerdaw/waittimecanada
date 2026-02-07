"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { clsx } from "clsx";

type PatternType = "hour_of_day" | "day_of_week" | "monthly";

interface TemporalPatternsProps {
  hospitalId: string;
}

interface PatternsResponse {
  success: boolean;
  data?: {
    hospital_id: string;
    hospital_name: string;
    pattern_type: PatternType;
    sample_count: number;
    patterns: Array<Record<string, string | number | null>>;
    insights: Record<string, string | number | null>;
  };
  error?: string;
}

const TABS: Array<{ key: PatternType; label: string }> = [
  { key: "hour_of_day", label: "Hour" },
  { key: "day_of_week", label: "Day" },
  { key: "monthly", label: "Monthly" },
];

function hourLabel(value: number): string {
  return `${value}:00`;
}

export function TemporalPatterns({ hospitalId }: TemporalPatternsProps) {
  const [tab, setTab] = useState<PatternType>("hour_of_day");
  const [payload, setPayload] = useState<PatternsResponse["data"] | null>(null);
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
          hospital_id: hospitalId,
          type: tab,
        });

        const response = await fetch(`/api/analytics/patterns?${query.toString()}`, {
          signal: controller.signal,
        });
        const json = (await response.json()) as PatternsResponse;

        if (!mounted) return;
        if (!response.ok || !json.success || !json.data) {
          setPayload(null);
          setError("Unable to load temporal patterns");
          setLoading(false);
          return;
        }

        setPayload(json.data);
        setLoading(false);
      } catch (err) {
        if (!mounted || (err as Error).name === "AbortError") return;
        console.error(err);
        setPayload(null);
        setError("Unable to load temporal patterns");
        setLoading(false);
      }
    }

    load();

    return () => {
      mounted = false;
      controller.abort();
    };
  }, [hospitalId, tab]);

  const chartData = useMemo(() => payload?.patterns ?? [], [payload]);

  const hasData = chartData.some((row) => row.mean !== null && row.mean !== undefined);

  const hourInsights = payload?.insights as
    | {
        peak_hour: number | null;
        quietest_hour: number | null;
        peak_mean: number | null;
        quietest_mean: number | null;
        peak_vs_quiet_ratio: number | null;
      }
    | undefined;

  const dayInsights = payload?.insights as
    | {
        worst_day: string | null;
        best_day: string | null;
        weekend_vs_weekday_ratio: number | null;
      }
    | undefined;

  const monthInsights = payload?.insights as
    | {
        direction: "improving" | "stable" | "worsening";
        change_percent: number;
        start_mean: number | null;
        end_mean: number | null;
      }
    | undefined;

  return (
    <div className="rounded-xl border border-border/40 bg-card p-3">
      <div className="flex items-center justify-between gap-2 mb-3">
        <p className="text-[10px] uppercase tracking-wide font-semibold text-muted-foreground">
          Temporal Patterns
        </p>
        {payload && (
          <span className="text-[10px] text-muted-foreground">
            {payload.sample_count} samples
          </span>
        )}
      </div>

      <div className="inline-flex items-center gap-1 rounded-lg border border-border/50 bg-muted/30 p-1 mb-3">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setTab(item.key)}
            className={clsx(
              "px-2.5 py-1 text-xs rounded-md font-medium transition-colors",
              tab === item.key
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-background/70"
            )}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="h-[180px] w-full">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center text-xs text-red-600">{error}</div>
        ) : !hasData ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            Not enough pattern data yet
          </div>
        ) : tab === "monthly" ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="mean"
                stroke="var(--primary)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis
                dataKey={tab === "hour_of_day" ? "hour" : "day"}
                tickFormatter={(value) =>
                  tab === "hour_of_day" ? hourLabel(Number(value)) : String(value)
                }
                tick={{ fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                interval={tab === "hour_of_day" ? 3 : 0}
              />
              <YAxis tick={{ fontSize: 10 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip
                labelFormatter={(value) =>
                  tab === "hour_of_day" ? `Hour: ${hourLabel(Number(value))}` : String(value)
                }
              />
              <Bar dataKey="mean" fill="var(--primary)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {!loading && !error && hasData && tab === "hour_of_day" && hourInsights && (
        <p className="mt-2 text-[10px] text-muted-foreground">
          Peak at {hourInsights.peak_hour}:00 ({hourInsights.peak_mean} min), quietest at
          {" "}
          {hourInsights.quietest_hour}:00 ({hourInsights.quietest_mean} min).
          {" "}
          {hourInsights.peak_vs_quiet_ratio}x difference.
        </p>
      )}

      {!loading && !error && hasData && tab === "day_of_week" && dayInsights && (
        <p className="mt-2 text-[10px] text-muted-foreground">
          Busiest: {dayInsights.worst_day}. Best: {dayInsights.best_day}. Weekend/weekday ratio:
          {" "}
          {dayInsights.weekend_vs_weekday_ratio}.
        </p>
      )}

      {!loading && !error && hasData && tab === "monthly" && monthInsights && (
        <p className="mt-2 text-[10px] text-muted-foreground">
          Trend: {monthInsights.direction} ({monthInsights.change_percent}% change). From
          {" "}
          {monthInsights.start_mean} to {monthInsights.end_mean} minutes.
        </p>
      )}
    </div>
  );
}
