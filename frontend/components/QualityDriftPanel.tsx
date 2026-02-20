"use client";

import { useState, useEffect } from "react";

interface QualityDriftPanelProps {
  sources: { source_id: string; source_name: string; province: string }[];
}

interface SourceDiff {
  source_id: string;
  source_name: string;
  province: string;
  diff: any | null;
  loading: boolean;
  error: boolean;
}

export function QualityDriftPanel({ sources }: QualityDriftPanelProps) {
  const [diffs, setDiffs] = useState<SourceDiff[]>([]);

  useEffect(() => {
    let mounted = true;

    // Initialize state
    const initialDiffs = sources.map((s) => ({
      ...s,
      diff: null,
      loading: true,
      error: false,
    }));
    setDiffs(initialDiffs);

    // Fetch diff for each source
    sources.forEach((source) => {
      fetch(`/api/data-quality?view=diff&source_id=${source.source_id}&compare_days=7`)
        .then((r) => {
          if (!r.ok) throw new Error("Failed");
          return r.json();
        })
        .then((data) => {
          if (!mounted) return;
          setDiffs((prev) =>
            prev.map((d) =>
              d.source_id === source.source_id
                ? { ...d, diff: data, loading: false }
                : d,
            ),
          );
        })
        .catch(() => {
          if (!mounted) return;
          setDiffs((prev) =>
            prev.map((d) =>
              d.source_id === source.source_id
                ? { ...d, loading: false, error: true }
                : d,
            ),
          );
        });
    });

    return () => {
      mounted = false;
    };
  }, [sources]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {diffs.map((item) => (
        <div
          key={item.source_id}
          className="rounded-lg border border-border/50 bg-card p-4 flex flex-col gap-3"
        >
          <div className="flex justify-between items-center">
            <h4 className="font-medium text-sm">
              {item.province} - {item.source_name}
            </h4>
          </div>

          {item.loading ? (
            <div className="animate-pulse flex gap-2 w-full h-12 bg-muted/20 rounded"></div>
          ) : item.error ? (
            <div className="text-sm text-red-500">Failed to load diff</div>
          ) : !item.diff?.has_baseline ? (
            <div className="text-sm text-muted-foreground p-2 bg-muted/10 rounded">
              No baseline data yet.
            </div>
          ) : (
            <>
              <p className="text-xs text-muted-foreground leading-relaxed h-8">
                {item.diff.summary}
              </p>
              <div className="flex gap-4 border-t border-border/50 pt-3 mt-1">
                <div className="flex-1">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                    Coverage
                  </div>
                  <div
                    className={`font-semibold text-sm ${
                      item.diff.deltas.success_rate_delta > 0.02
                        ? "text-emerald-600 dark:text-emerald-400"
                        : item.diff.deltas.success_rate_delta < -0.02
                          ? "text-red-600 dark:text-red-400"
                          : "text-foreground"
                    }`}
                  >
                    {item.diff.deltas.success_rate_delta > 0 ? "+" : ""}
                    {(item.diff.deltas.success_rate_delta * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="flex-1">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                    Hospitals
                  </div>
                  <div className="font-semibold text-sm text-foreground">
                    {item.diff.deltas.hospitals_reporting_delta > 0 ? "+" : ""}
                    {item.diff.deltas.hospitals_reporting_delta}
                  </div>
                </div>
                <div className="flex-1">
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                    Worst Gap
                  </div>
                  <div
                    className={`font-semibold text-sm ${
                      item.diff.deltas.worst_gap_delta < -30
                        ? "text-emerald-600 dark:text-emerald-400" // Reduced gap is good
                        : item.diff.deltas.worst_gap_delta > 30
                          ? "text-red-600 dark:text-red-400" // Increased gap is bad
                          : "text-foreground"
                    }`}
                  >
                    {item.diff.deltas.worst_gap_delta > 0 ? "+" : ""}
                    {item.diff.deltas.worst_gap_delta}m
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
