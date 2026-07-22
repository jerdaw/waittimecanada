"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { useTranslations } from "next-intl";
import { CheckCircle, AlertTriangle, XCircle, HelpCircle } from "lucide-react";

interface SourceStatus {
  source_id: string;
  source_name: string;
  province: string;
  uptime_24h: number;
  uptime_7d: number;
  uptime_30d: number;
  total_hospitals: number;
  last_heartbeat_age_minutes: number | null;
  scraper_status: string;
  last_run: string | null;
}

interface DriftEvent {
  source_id: string;
  previous_period_start: string;
  current_period_start: string;
  previous_mean: number;
  current_mean: number;
  shift_percent: number;
  hospitals_analyzed: number;
  explanation: string;
  detected_at: string;
}

interface SystemStatus {
  overall_status: "healthy" | "degraded" | "critical";
  overall_status_basis: "measurement_hour_completeness_24h";
  measurement_window_timezone: "UTC";
  system_uptime_24h: number;
  sources: SourceStatus[];
  drift_events: DriftEvent[];
  generated_at: string;
}

function StatusBadge({
  status,
  t,
}: {
  status: string;
  t: ReturnType<typeof useTranslations>;
}) {
  const styles: Record<string, string> = {
    healthy:
      "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
    degraded:
      "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
    critical: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
    unknown: "bg-gray-100 dark:bg-gray-800 text-gray-500",
  };
  const icons: Record<string, React.ReactNode> = {
    healthy: <CheckCircle className="w-3 h-3" aria-hidden="true" />,
    degraded: <AlertTriangle className="w-3 h-3" aria-hidden="true" />,
    critical: <XCircle className="w-3 h-3" aria-hidden="true" />,
    unknown: <HelpCircle className="w-3 h-3" aria-hidden="true" />,
  };
  const key = status as "healthy" | "degraded" | "critical" | "unknown";
  const label = t(`status.${key in styles ? key : "unknown"}`);
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${styles[status] ?? styles.unknown}`}
    >
      {icons[status] ?? icons.unknown}
      {label}
    </span>
  );
}

function UptimeBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 95 ? "bg-green-500" : pct >= 80 ? "bg-amber-400" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs tabular-nums text-muted-foreground w-10 text-right">
        {pct}%
      </span>
    </div>
  );
}

function HeartbeatAge({ minutes }: { minutes: number | null }) {
  if (minutes === null) return <span className="text-muted-foreground">—</span>;
  const color =
    minutes < 30
      ? "text-green-600 dark:text-green-400"
      : minutes < 90
        ? "text-amber-600 dark:text-amber-400"
        : "text-red-600 dark:text-red-400";
  return (
    <span className={`tabular-nums ${color}`}>
      {minutes < 60 ? `${minutes}m ago` : `${Math.round(minutes / 60)}h ago`}
    </span>
  );
}

function SourceCard({
  source,
  t,
}: {
  source: SourceStatus;
  t: ReturnType<typeof useTranslations>;
}) {
  const scraperOk = source.scraper_status === "healthy";
  const overallStatus =
    source.uptime_24h >= 0.95
      ? "healthy"
      : source.uptime_24h >= 0.8
        ? "degraded"
        : "critical";

  return (
    <div
      data-testid="source-card"
      className="rounded-xl border border-border/50 bg-card p-4 space-y-3"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-sm text-foreground">
            {source.source_name}
          </p>
          <p className="text-xs text-muted-foreground">{source.province}</p>
        </div>
        <StatusBadge status={overallStatus} t={t} />
      </div>

      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-muted-foreground mb-0.5">
          <span>{t("uptime.24h")}</span>
        </div>
        <UptimeBar value={source.uptime_24h} />
        <div className="flex justify-between text-xs text-muted-foreground mb-0.5">
          <span>{t("uptime.7d")}</span>
        </div>
        <UptimeBar value={source.uptime_7d} />
        <div className="flex justify-between text-xs text-muted-foreground mb-0.5">
          <span>{t("uptime.30d")}</span>
        </div>
        <UptimeBar value={source.uptime_30d} />
      </div>

      <div className="flex items-center justify-between text-xs border-t border-border/40 pt-2">
        <span className="text-muted-foreground">
          {t("scraper.hospitals", { count: source.total_hospitals })} ·{" "}
          {t("scraper.label")}{" "}
          <span
            className={
              scraperOk ? "text-green-600 dark:text-green-400" : "text-red-500"
            }
          >
            {scraperOk ? t("scraper.active") : source.scraper_status}
          </span>
        </span>
        <HeartbeatAge minutes={source.last_heartbeat_age_minutes} />
      </div>
    </div>
  );
}

const REFRESH_INTERVAL = 5 * 60_000;

export default function StatusPage() {
  const t = useTranslations("StatusPage");
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(() => {
    fetch("/api/status")
      .then((r) => r.json())
      .then((data: SystemStatus) => {
        setStatus(data);
        setLoading(false);
        setError(null);
      })
      .catch(() => {
        setError(t("error"));
        setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchStatus();

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        fetchStatus();
      }
    };

    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        fetchStatus();
      }
    }, REFRESH_INTERVAL);

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [fetchStatus]);

  return (
    <main className="min-h-screen bg-muted/20 flex flex-col">
      <Header />

      <div className="max-w-screen-lg mx-auto px-4 sm:px-6 py-8 space-y-8 flex-1">
        {/* Page header */}
        <section>
          <Link href="/" className="text-sm text-primary hover:underline">
            {t("backToMap")}
          </Link>
          <h1 className="text-3xl font-bold text-foreground mt-2">
            {t("title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            {t("subtitle")}
          </p>
        </section>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-16 text-red-500">{error}</div>
        ) : status ? (
          <>
            {/* Overall health banner */}
            <section
              className="rounded-xl border border-border/50 bg-card p-6"
              data-testid="overall-status"
            >
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-xl font-semibold">{t("overallHealth")}</h2>
                <StatusBadge status={status.overall_status} t={t} />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold tabular-nums">
                    {Math.round(status.system_uptime_24h * 100)}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {t("systemUptime24h")}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold tabular-nums">
                    {status.sources.length}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {t("activeProvinces")}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold tabular-nums">
                    {status.sources.reduce(
                      (acc, s) => acc + s.total_hospitals,
                      0,
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {t("hospitalsTracked")}
                  </div>
                </div>
              </div>
            </section>

            {/* Per-province cards */}
            <section>
              <h2 className="text-xl font-semibold mb-4">
                {t("provincialScrapers")}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {status.sources.map((source) => (
                  <SourceCard key={source.source_id} source={source} t={t} />
                ))}
              </div>
            </section>

            {/* Methodology drift events */}
            <section>
              <h2 className="text-xl font-semibold mb-2">{t("driftEvents")}</h2>
              <p className="text-sm text-muted-foreground mb-4">
                {t("driftEventsDesc")}
              </p>
              {status.drift_events.length === 0 ? (
                <div className="rounded-xl border border-border/50 bg-card p-6 text-center text-sm text-muted-foreground flex items-center justify-center gap-2">
                  <CheckCircle
                    className="w-4 h-4 text-green-500"
                    aria-hidden="true"
                  />
                  {t("noDriftEvents")}
                </div>
              ) : (
                <div className="space-y-3">
                  {status.drift_events.map((event, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700 p-4"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="font-medium text-sm text-amber-900 dark:text-amber-200">
                          {event.source_id}
                        </span>
                        <span className="text-xs text-amber-700 dark:text-amber-400 tabular-nums">
                          {new Date(event.detected_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs text-amber-800 dark:text-amber-300">
                        {event.explanation}
                      </p>
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                        {event.previous_mean} min → {event.current_mean} min (
                        {event.shift_percent > 0 ? "+" : ""}
                        {event.shift_percent.toFixed(1)}%) across{" "}
                        {event.hospitals_analyzed} hospitals
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Footer note */}
            <section className="rounded-xl border border-border/50 bg-card p-5 text-sm text-muted-foreground space-y-2">
              <p>
                <strong className="text-foreground">
                  {t("dataFreshness")}
                </strong>{" "}
                {t("statusGeneratedAt", {
                  time: new Date(status.generated_at).toLocaleString(),
                })}
              </p>
              <p>
                <strong className="text-foreground">{t("uptimeCalc")}</strong>{" "}
                {t("uptimeCalcDesc")}
              </p>
              <p>
                {t("detailedQuality")}{" "}
                <Link
                  href="/data-quality"
                  className="text-primary hover:underline"
                >
                  {t("dataQualityDashboard")}
                </Link>
                .
              </p>
            </section>
          </>
        ) : null}
      </div>

      <Footer />
    </main>
  );
}
