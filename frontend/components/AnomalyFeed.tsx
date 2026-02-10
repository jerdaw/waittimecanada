"use client";
import { useState, useEffect } from "react";

interface Anomaly {
  id: number;
  hospital_id: string;
  hospital_name: string;
  province: string;
  value: number;
  timestamp: string;
  reason: string;
  source_id: string;
}

interface AnomalyFeedProps {
  sourceId?: string;
  days?: number;
}

export function AnomalyFeed({ sourceId, days = 7 }: AnomalyFeedProps) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const params = new URLSearchParams();
    params.set("days", String(days));
    if (sourceId) params.set("source_id", sourceId);

    fetch(`/api/anomalies?${params}`)
      .then((r) => r.json())
      .then((data) => {
        if (mounted) {
          setAnomalies(data.anomalies ?? []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError("Failed to load anomalies");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [sourceId, days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-6">
        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-red-500 text-center py-4">{error}</div>;
  }

  if (anomalies.length === 0) {
    return (
      <div className="text-sm text-muted-foreground text-center py-6">
        No anomalies detected in the last {days} days
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid="anomaly-feed">
      {anomalies.map((a) => (
        <div
          key={a.id}
          className="flex items-start gap-3 p-3 rounded-lg border border-border/50 bg-card hover:bg-muted/30 transition-colors"
        >
          <div className="mt-0.5">
            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-100 dark:bg-amber-900/30">
              <svg
                className="w-3 h-3 text-amber-600 dark:text-amber-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="font-medium text-sm truncate">
                {a.hospital_name}
              </span>
              <span className="text-xs text-muted-foreground">
                ({a.province})
              </span>
            </div>
            <div className="text-xs text-muted-foreground mb-1">
              {new Date(a.timestamp).toLocaleString()}
            </div>
            <div className="text-sm">
              <span className="font-semibold text-amber-600 dark:text-amber-400">
                {a.value} min
              </span>
              <span className="text-muted-foreground"> — {a.reason}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
