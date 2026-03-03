"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Area,
  ComposedChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DataQualityCard } from "@/components/DataQualityCard";
import { AnomalyFeed } from "@/components/AnomalyFeed";
import { QualityDriftPanel } from "@/components/QualityDriftPanel";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { useTranslations } from "next-intl";

interface SourceQuality {
  source_id: string;
  source_name: string;
  province: string;
  last_24h_success_rate: number;
  last_7d_success_rate: number;
  hospitals_reporting: number;
  total_hospitals: number;
  last_heartbeat_age_minutes: number | null;
  scraper_status: string;
}

interface SystemQuality {
  overall_status: "healthy" | "degraded" | "critical";
  sources: SourceQuality[];
  system_uptime_24h: number;
  total_measurements_24h: number;
  total_hospitals_reporting: number;
}

function getStatusBadge(status: string) {
  const styles: Record<string, string> = {
    healthy:
      "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
    degraded:
      "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
    critical: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  };
  return styles[status] ?? styles.critical;
}

function QualityTrendSection({
  sourceId,
  sourceName,
  t,
}: {
  sourceId: string;
  sourceName: string;
  t: ReturnType<typeof useTranslations>;
}) {
  const [trend, setTrend] = useState<any>(null);
  const [diff, setDiff] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    Promise.all([
      fetch(`/api/data-quality?view=trend&source_id=${sourceId}&days=30`).then(
        (r) => r.json(),
      ),
      fetch(
        `/api/data-quality?view=diff&source_id=${sourceId}&compare_days=7`,
      ).then((r) => r.json()),
    ])
      .then(([trendData, diffData]) => {
        if (!mounted) return;
        setTrend(trendData.trend?.reverse() || []);
        setDiff(diffData);
        setLoading(false);
      })
      .catch(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [sourceId]);

  if (loading) {
    return <div className="animate-pulse h-48 bg-muted/20 rounded-lg"></div>;
  }

  if (!trend || trend.length === 0) {
    return (
      <div className="text-sm text-muted-foreground p-4 text-center border rounded-lg bg-card">
        {t("noHistoricalData", { sourceName })}
      </div>
    );
  }

  const chartData = trend.map((row: any) => {
    const d = new Date(row.snapshot_date);
    return {
      ...row,
      success_pct: row.avg_success_rate * 100,
      label: `${d.getUTCMonth() + 1}/${d.getUTCDate()}`,
    };
  });

  return (
    <div className="space-y-4">
      {diff?.has_baseline && (
        <div className="rounded-lg border border-border/50 bg-card p-4 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
          <div>
            <h4 className="font-medium text-sm">{t("delta7d")}</h4>
            <p className="text-sm text-muted-foreground mt-1">{diff.summary}</p>
          </div>
          <div className="flex gap-6">
            <div className="text-center">
              <div className="text-xs text-muted-foreground">
                {t("coverage")}
              </div>
              <div
                className={`font-semibold ${
                  diff.deltas.success_rate_delta > 0.02
                    ? "text-emerald-600 dark:text-emerald-400"
                    : diff.deltas.success_rate_delta < -0.02
                      ? "text-red-600 dark:text-red-400"
                      : "text-foreground"
                }`}
              >
                {diff.deltas.success_rate_delta > 0 ? "+" : ""}
                {(diff.deltas.success_rate_delta * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-muted-foreground">
                {t("hospitals")}
              </div>
              <div className="font-semibold text-foreground">
                {diff.deltas.hospitals_reporting_delta > 0 ? "+" : ""}
                {diff.deltas.hospitals_reporting_delta}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="h-[240px] w-full rounded-lg border border-border/50 bg-card p-4">
        <h4 className="text-sm font-medium mb-4">{t("successRate30d")}</h4>
        <ResponsiveContainer width="100%" height="80%">
          <ComposedChart
            data={chartData}
            margin={{ top: 5, right: 0, left: -20, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="var(--border)"
            />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              domain={[0, 100]}
            />
            <Tooltip
              formatter={(value: number | undefined) => [
                `${(value ?? 0).toFixed(1)}%`,
                "Success Rate",
              ]}
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "0.5rem",
              }}
              labelStyle={{ color: "var(--foreground)" }}
            />
            <Area
              type="monotone"
              dataKey="success_pct"
              fill="var(--primary)"
              fillOpacity={0.15}
              stroke="var(--primary)"
              strokeWidth={2}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function DataQualityPage() {
  const t = useTranslations("DataQualityPage");
  const [quality, setQuality] = useState<SystemQuality | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<string>("");

  useEffect(() => {
    fetch("/api/data-quality")
      .then((r) => r.json())
      .then((data) => {
        setQuality(data);
        if (data.sources && data.sources.length > 0) {
          setSelectedSourceId(data.sources[0].source_id);
        }
        setLoading(false);
      })
      .catch(() => {
        setError(t("error"));
        setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Header />

      <div className="container max-w-5xl mx-auto px-4 sm:px-6 py-8 flex-1">
        {/* Page Header */}
        <div className="mb-8">
          <Link href="/" className="text-sm text-primary hover:underline">
            {t("backToMap")}
          </Link>
          <h1 className="text-3xl font-bold text-foreground mt-2">
            {t("title")}
          </h1>
          <p className="text-muted-foreground text-sm max-w-3xl mt-1">
            {t("subtitle")}
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-16 text-red-500">{error}</div>
        ) : quality ? (
          <div className="space-y-8">
            {/* System Health Summary */}
            <section>
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-xl font-semibold">{t("systemHealth")}</h2>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${getStatusBadge(quality.overall_status)}`}
                >
                  {quality.overall_status.charAt(0).toUpperCase() +
                    quality.overall_status.slice(1)}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="rounded-xl border border-border/50 bg-card p-4 text-center shadow-sm">
                  <div className="text-2xl font-bold tabular-nums">
                    {(quality.system_uptime_24h * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {t("uptime24h")}
                  </div>
                </div>
                <div className="rounded-xl border border-border/50 bg-card p-4 text-center shadow-sm">
                  <div className="text-2xl font-bold tabular-nums">
                    {quality.total_measurements_24h.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {t("measurements24h")}
                  </div>
                </div>
                <div className="rounded-xl border border-border/50 bg-card p-4 text-center shadow-sm">
                  <div className="text-2xl font-bold tabular-nums">
                    {quality.total_hospitals_reporting}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {t("hospitalsReporting")}
                  </div>
                </div>
              </div>

              {/* Per-source cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {quality.sources.map((source) => (
                  <DataQualityCard key={source.source_id} source={source} />
                ))}
              </div>
            </section>

            {/* 7-Day Quality Drift */}
            <section>
              <h2 className="text-xl font-semibold mb-2">
                {t("qualityDrift")}
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                {t("qualityDriftDesc")}
              </p>
              <QualityDriftPanel sources={quality.sources} />
            </section>

            {/* Recent Anomalies */}
            <section>
              <h2 className="text-xl font-semibold mb-2">
                {t("recentAnomalies")}
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                {t("recentAnomaliesDesc")}
              </p>
              <AnomalyFeed />
            </section>

            {/* Quality Trend */}
            <section>
              <h2 className="text-xl font-semibold mb-2">
                {t("qualityTrend")}
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                {t("qualityTrendDesc")}
              </p>
              <div className="mb-4">
                <select
                  className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                  value={selectedSourceId}
                  onChange={(e) => setSelectedSourceId(e.target.value)}
                >
                  {quality.sources.map((s) => (
                    <option key={s.source_id} value={s.source_id}>
                      {s.province} - {s.source_name}
                    </option>
                  ))}
                </select>
              </div>
              {selectedSourceId && (
                <QualityTrendSection
                  sourceId={selectedSourceId}
                  sourceName={
                    quality.sources.find(
                      (s) => s.source_id === selectedSourceId,
                    )?.source_name || selectedSourceId
                  }
                  t={t}
                />
              )}
            </section>

            {/* Methodology Notes — card layout */}
            <section className="rounded-xl border border-border/50 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-4">
                {t("aboutMetrics")}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-lg border border-border/40 p-4">
                  <p className="font-medium text-foreground text-sm mb-1">
                    {t("metrics.successRate")}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {t("metrics.successRateDesc")}
                  </p>
                </div>
                <div className="rounded-lg border border-border/40 p-4">
                  <p className="font-medium text-foreground text-sm mb-1">
                    {t("metrics.anomalyDetection")}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {t("metrics.anomalyDetectionDesc")}
                  </p>
                </div>
                <div className="rounded-lg border border-border/40 p-4">
                  <p className="font-medium text-foreground text-sm mb-1">
                    {t("metrics.whyTransparency")}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {t("metrics.whyTransparencyDesc")}
                  </p>
                </div>
              </div>
            </section>
          </div>
        ) : null}
      </div>

      <Footer />
    </main>
  );
}
