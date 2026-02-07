"use client";

import { Hospital } from "@/app/api/hospitals/route";
import { clsx } from "clsx";
import { useEffect, useState } from "react";

type TrendDirection = "improving" | "stable" | "worsening";

interface BenchmarkHospital {
  hospital_id: string;
  hospital_name: string;
  city: string;
  current_wait: number | null;
  period_mean: number;
  percentile: number;
  quartile: 1 | 2 | 3 | 4;
  trend: TrendDirection;
  trend_change_percent: number;
}

interface BenchmarksApiResponse {
  success: boolean;
  data?: {
    province: string;
    period: string;
    generated_at: string;
    hospital_count: number;
    province_stats: {
      mean: number | null;
      median: number | null;
      p25: number | null;
      p75: number | null;
      min: number | null;
      max: number | null;
    };
    hospitals: BenchmarkHospital[];
  };
  error?: string;
}

interface BenchmarkCardProps {
  hospital: Hospital;
  compact?: boolean;
}

function formatOrdinal(value: number): string {
  const tens = value % 100;
  if (tens >= 11 && tens <= 13) return `${value}th`;

  const ones = value % 10;
  if (ones === 1) return `${value}st`;
  if (ones === 2) return `${value}nd`;
  if (ones === 3) return `${value}rd`;
  return `${value}th`;
}

function quartileLabel(quartile: number): string {
  if (quartile === 1) return "Q1 - Lower Waits";
  if (quartile === 2) return "Q2 - Typical Waits";
  if (quartile === 3) return "Q3 - Above Typical";
  return "Q4 - Highest Waits";
}

function quartileClasses(quartile: number): string {
  if (quartile === 1) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (quartile === 2 || quartile === 3) return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-red-50 text-red-700 border-red-200";
}

function trendIndicator(trend: TrendDirection): { symbol: string; className: string; label: string } {
  if (trend === "improving") {
    return { symbol: "v", className: "text-emerald-700", label: "Improving" };
  }
  if (trend === "worsening") {
    return { symbol: "^", className: "text-red-700", label: "Worsening" };
  }
  return { symbol: "-", className: "text-slate-600", label: "Stable" };
}

function provinceLabel(code: string): string {
  const labels: Record<string, string> = {
    ON: "Ontario",
    QC: "Quebec",
    AB: "Alberta",
    BC: "British Columbia",
    MB: "Manitoba",
    SK: "Saskatchewan",
    NS: "Nova Scotia",
    NB: "New Brunswick",
    NL: "Newfoundland and Labrador",
    PE: "Prince Edward Island",
    NT: "Northwest Territories",
    NU: "Nunavut",
    YT: "Yukon",
  };

  return labels[code] ?? code;
}

export function BenchmarkCard({ hospital, compact = false }: BenchmarkCardProps) {
  const [benchmark, setBenchmark] = useState<BenchmarkHospital | null>(null);
  const [provinceMean, setProvinceMean] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hospital.id || !hospital.province) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function loadBenchmark() {
      try {
        setLoading(true);
        const query = new URLSearchParams({
          province: hospital.province,
          period: "7d",
          hospital_id: hospital.id,
        });

        const response = await fetch(`/api/analytics/benchmarks?${query.toString()}`, {
          signal: controller.signal,
        });

        const payload = (await response.json()) as BenchmarksApiResponse;
        if (!response.ok || !payload.success || !payload.data) {
          setBenchmark(null);
          setProvinceMean(null);
          return;
        }

        setBenchmark(payload.data.hospitals[0] ?? null);
        setProvinceMean(payload.data.province_stats.mean);
      } catch (error) {
        if ((error as Error).name === "AbortError") return;
        console.error("Failed to fetch benchmark data:", error);
        setBenchmark(null);
        setProvinceMean(null);
      } finally {
        setLoading(false);
      }
    }

    loadBenchmark();
    return () => controller.abort();
  }, [hospital.id, hospital.province]);

  if (!loading && !benchmark) {
    return null;
  }

  const trend = benchmark ? trendIndicator(benchmark.trend) : null;

  if (compact) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
        {loading || !benchmark || !trend ? (
          <div className="text-xs text-slate-500">Loading benchmark...</div>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-2 text-xs">
              <span className="font-semibold text-slate-700">Peer Rank</span>
              <span className={clsx("font-semibold", trend.className)}>
                {trend.symbol} {Math.abs(benchmark.trend_change_percent).toFixed(1)}%
              </span>
            </div>
            <div className="text-xs text-slate-700">
              {formatOrdinal(benchmark.percentile)} percentile ({quartileLabel(benchmark.quartile)})
            </div>
            {provinceMean !== null && (
              <div className="text-[11px] text-slate-500">
                Province avg: {Math.round(provinceMean)} min
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border/40 bg-gradient-to-br from-muted/30 to-muted/10 p-3">
      <div className="flex items-center justify-between gap-2 mb-2">
        <p className="text-[10px] uppercase tracking-wide font-semibold text-muted-foreground">
          Peer Benchmark ({provinceLabel(hospital.province)})
        </p>
        {loading && <span className="text-[10px] text-muted-foreground">Loading...</span>}
      </div>

      {!loading && benchmark && trend && (
        <>
          <div className="flex items-center justify-between gap-2 mb-2">
            <span
              className={clsx(
                "text-xs font-semibold px-2 py-1 rounded-full border",
                quartileClasses(benchmark.quartile)
              )}
            >
              {formatOrdinal(benchmark.percentile)} percentile wait time
            </span>
            <span className={clsx("text-xs font-semibold", trend.className)}>
              {trend.symbol} {trend.label} ({Math.abs(benchmark.trend_change_percent).toFixed(1)}%)
            </span>
          </div>

          <p className="text-xs text-foreground mb-1">{quartileLabel(benchmark.quartile)}</p>

          <p className="text-xs text-muted-foreground">
            {provinceMean !== null
              ? `${provinceLabel(hospital.province)} avg: ${Math.round(
                  provinceMean
                )} min | This hospital: ${Math.round(benchmark.period_mean)} min`
              : `This hospital: ${Math.round(benchmark.period_mean)} min (7-day mean)`}
          </p>

          <p className="mt-2 text-[10px] text-muted-foreground">
            Rankings reflect 7-day averages. Lower percentile indicates shorter waits.
          </p>
        </>
      )}
    </div>
  );
}
