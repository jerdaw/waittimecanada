"use client";
import { useState, useEffect } from "react";
import { DataQualityCard } from "@/components/DataQualityCard";
import { AnomalyFeed } from "@/components/AnomalyFeed";

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
    healthy: "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300",
    degraded: "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
    critical: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  };
  return styles[status] ?? styles.critical;
}

export default function DataQualityPage() {
  const [quality, setQuality] = useState<SystemQuality | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/data-quality")
      .then((r) => r.json())
      .then((data) => {
        setQuality(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load data quality metrics");
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen bg-background">
      <div className="container max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold mb-2">Data Quality & Provenance</h1>
          <p className="text-muted-foreground text-sm max-w-2xl">
            Transparent metrics about our data collection reliability. Every measurement
            is tracked, gaps are detected, and statistical outliers are flagged — because
            research-grade data requires research-grade auditing.
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
                <h2 className="text-lg font-semibold">System Health</h2>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${getStatusBadge(quality.overall_status)}`}
                >
                  {quality.overall_status.charAt(0).toUpperCase() + quality.overall_status.slice(1)}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-card rounded-lg border border-border/50 p-3 text-center">
                  <div className="text-2xl font-bold tabular-nums">
                    {(quality.system_uptime_24h * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground">24h Uptime</div>
                </div>
                <div className="bg-card rounded-lg border border-border/50 p-3 text-center">
                  <div className="text-2xl font-bold tabular-nums">
                    {quality.total_measurements_24h.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground">Measurements (24h)</div>
                </div>
                <div className="bg-card rounded-lg border border-border/50 p-3 text-center">
                  <div className="text-2xl font-bold tabular-nums">
                    {quality.total_hospitals_reporting}
                  </div>
                  <div className="text-xs text-muted-foreground">Hospitals Reporting</div>
                </div>
              </div>

              {/* Per-source cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {quality.sources.map((source) => (
                  <DataQualityCard key={source.source_id} source={source} />
                ))}
              </div>
            </section>

            {/* Recent Anomalies */}
            <section>
              <h2 className="text-lg font-semibold mb-4">Recent Anomalies</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Measurements flagged as statistical outliers. These are still included in the
                dataset — the flag is metadata for transparency, not a filter.
              </p>
              <AnomalyFeed />
            </section>

            {/* Methodology Notes */}
            <section className="bg-card rounded-lg border border-border/50 p-6">
              <h2 className="text-lg font-semibold mb-3">About Data Quality Metrics</h2>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div>
                  <strong className="text-foreground">Success Rate:</strong> Scrapers run
                  every 15 minutes (96 expected per day per hospital). Success rate measures
                  actual vs expected data collection.
                </div>
                <div>
                  <strong className="text-foreground">Anomaly Detection:</strong> Uses z-score
                  (3 standard deviations) and IQR methods against a 7-day rolling baseline.
                  Requires 20+ historical data points before flagging.
                </div>
                <div>
                  <strong className="text-foreground">Why Transparency Matters:</strong> Clinical
                  researchers need to know data reliability before drawing conclusions. We expose
                  every gap, outlier, and quality metric because that is what research-grade
                  infrastructure demands.
                </div>
              </div>
            </section>
          </div>
        ) : null}
      </div>
    </main>
  );
}
