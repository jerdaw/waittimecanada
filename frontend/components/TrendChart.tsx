"use client";
import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { clsx } from "clsx";

type Period = "24h" | "7d" | "30d";

interface TrendChartProps {
  hospitalId: string;
}

export function TrendChart({ hospitalId }: TrendChartProps) {
  const [period, setPeriod] = useState<Period>("24h");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [data, setData] = useState<any>(null);
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
          setError("Failed to load trends");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [hospitalId, period]);

  // Format tick labels
  const formatXAxis = (tickItem: string) => {
    const date = new Date(tickItem);
    if (period === "24h") {
      return date.toLocaleTimeString([], { hour: "numeric", hour12: true });
    }
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const formatTooltip = (value: any) => [`${value} min`, "Wait Time"];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const formatTooltipLabel = (label: any) => {
    if (!label) return "";
    const date = new Date(label);
    return date.toLocaleString();
  };

  return (
    <div className="bg-card rounded-lg p-4 border border-border/50 shadow-sm mt-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-sm">Wait Time Trends</h3>
        <div className="flex gap-1 bg-muted/50 p-1 rounded-md">
          {(["24h", "7d", "30d"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={clsx(
                "px-2 py-1 text-xs rounded font-medium transition-colors",
                period === p
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              )}
            >
              {p}
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
            No historical data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.dataPoints}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
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
                  fontSize: "12px"
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
