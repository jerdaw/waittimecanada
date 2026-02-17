import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ComposedChart,
} from "recharts";
import { clsx } from "clsx";
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent";
import { useTranslations } from "next-intl";

type Period = "24h" | "7d" | "30d" | "90d" | "6m" | "1y";

interface TrendDataPoint {
  timestamp: string;
  waitTime: number;
  minWaitTime?: number;
  maxWaitTime?: number;
}

interface TrendData {
  dataPoints: TrendDataPoint[];
  dataSource: string;
  error?: string;
}

interface TrendChartProps {
  hospitalId: string;
}

export function TrendChart({ hospitalId }: TrendChartProps) {
  const t = useTranslations('TrendChart');
  const [period, setPeriod] = useState<Period>("24h");
  const [data, setData] = useState<TrendData | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    fetch(`/api/hospitals/${hospitalId}/trends?period=${period}`)
      .then((r) => r.json())
      .then((json) => {
        if (mounted) {
          if (json.error) throw new Error(json.error);
          setData(json);
          setLoading(false);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          console.error(err);
          setError(t('error'));
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [hospitalId, period, t]);

  const isAggregated = data?.dataSource === "aggregated";
  const hasMinMax = data?.dataPoints?.some(
    (d: TrendDataPoint) => d.minWaitTime != null && d.maxWaitTime != null,
  );

  // Format tick labels
  const formatXAxis = (tickItem: string) => {
    const date = new Date(tickItem);
    if (period === "24h") {
      return date.toLocaleTimeString([], { hour: "numeric", hour12: true });
    }
    if (period === "1y") {
      return date.toLocaleDateString([], { month: "short", year: "2-digit" });
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  const formatTooltip = (value: ValueType | undefined, name: NameType | undefined) => {
    if (name === "waitTime")
      return [`${value} min`, isAggregated ? t('mean') : t('waitTime')];
    if (name === "minWaitTime") return [`${value} min`, t('min')];
    if (name === "maxWaitTime") return [`${value} min`, t('max')];
    return [`${value}`, name ?? ""];
  };

  const formatTooltipLabel = (label: any) => {
    if (!label) return "";
    const date = new Date(label);
    return date.toLocaleString();
  };

  return (
    <div className="bg-card rounded-lg p-4 border border-border/50 shadow-sm mt-4">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-sm">{t('title')}</h3>
          {isAggregated && (
            <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded font-medium">
              {t('aggregated')}
            </span>
          )}
        </div>
        <div className="flex gap-1 bg-muted/50 p-1 rounded-md">
          {(["24h", "7d", "30d", "90d", "6m", "1y"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={clsx(
                "px-2 py-1 text-xs rounded font-medium transition-colors",
                period === p
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/50",
              )}
            >
              {t(`periods.${p}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="h-[200px] w-full">
        {loading ? (
          <div className="h-full w-full flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="h-full w-full flex items-center justify-center text-sm text-red-500">
            {error}
          </div>
        ) : !data?.dataPoints?.length ? (
          <div className="h-full w-full flex items-center justify-center text-sm text-muted-foreground">
            {t('noData')}
          </div>
        ) : hasMinMax ? (
          /* Aggregate view: mean line with min/max shaded area */
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data.dataPoints}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="var(--border)"
              />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                tickFormatter={formatXAxis}
                tickMargin={8}
                minTickGap={30}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                width={30}
                tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={formatTooltip}
                labelFormatter={formatTooltipLabel}
                contentStyle={{
                  backgroundColor: "var(--card)",
                  borderColor: "var(--border)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Area
                type="monotone"
                dataKey="maxWaitTime"
                fill="var(--primary)"
                fillOpacity={0.08}
                stroke="none"
              />
              <Area
                type="monotone"
                dataKey="minWaitTime"
                fill="var(--card)"
                fillOpacity={1}
                stroke="none"
              />
              <Line
                type="monotone"
                dataKey="waitTime"
                stroke="var(--primary)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: "var(--primary)" }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          /* Raw view: simple line chart */
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.dataPoints}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="var(--border)"
              />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                tickFormatter={formatXAxis}
                tickMargin={8}
                minTickGap={30}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                width={30}
                tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={formatTooltip}
                labelFormatter={formatTooltipLabel}
                contentStyle={{
                  backgroundColor: "var(--card)",
                  borderColor: "var(--border)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="waitTime"
                stroke="var(--primary)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: "var(--primary)" }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
