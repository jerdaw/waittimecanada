"use client";

import { clsx } from "clsx";

type RegionTrend = "improving" | "stable" | "worsening";

interface RegionAnalyticsRow {
  region_id: string;
  region_name: string;
  region_code: string;
  hospital_count: number;
  reporting_count: number;
  period_mean: number | null;
  period_median: number | null;
  best_wait: number | null;
  worst_wait: number | null;
  trend: RegionTrend;
  trend_change_percent: number;
  hospital_ids: string[];
  percentile: number | null;
  quartile: 1 | 2 | 3 | 4 | null;
}

interface RegionDashboardProps {
  province: string;
  period: string;
  regions: RegionAnalyticsRow[];
  provinceMean: number | null;
  mappingCoverage?: {
    mapped_hospitals: number;
    total_hospitals: number;
    coverage_percent: number;
  } | null;
  loading?: boolean;
  selectedRegionId: string | null;
  onSelectRegion: (regionId: string | null) => void;
}

function provinceLabel(code: string): string {
  const labels: Record<string, string> = {
    ON: "Ontario",
    QC: "Quebec",
    AB: "Alberta",
    BC: "British Columbia",
  };
  return labels[code] ?? code;
}

function formatWait(value: number | null): string {
  if (value === null) return "--";
  return `${Math.round(value)} min`;
}

function trendLabel(trend: RegionTrend, change: number): string {
  const pct = `${Math.abs(change).toFixed(1)}%`;
  if (trend === "improving") return `Improving ${pct}`;
  if (trend === "worsening") return `Worsening ${pct}`;
  return "Stable";
}

function trendClasses(trend: RegionTrend): string {
  if (trend === "improving") return "text-emerald-700 bg-emerald-50 border-emerald-200";
  if (trend === "worsening") return "text-red-700 bg-red-50 border-red-200";
  return "text-slate-700 bg-slate-50 border-slate-200";
}

function quartileClasses(quartile: 1 | 2 | 3 | 4 | null): string {
  if (quartile === 1) return "border-emerald-300 bg-emerald-50/60";
  if (quartile === 4) return "border-red-300 bg-red-50/60";
  return "border-border bg-card";
}

export function RegionDashboard({
  province,
  period,
  regions,
  provinceMean,
  mappingCoverage = null,
  loading = false,
  selectedRegionId,
  onSelectRegion,
}: RegionDashboardProps) {
  if (!loading && regions.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-border/50 bg-card p-4">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Regional Intelligence</h3>
          <p className="text-xs text-muted-foreground">
            {provinceLabel(province)} health regions, {period} averages
          </p>
        </div>
        <button
          onClick={() => onSelectRegion(null)}
          className="text-xs text-primary hover:underline"
          type="button"
        >
          Clear Region Filter
        </button>
      </div>

      {provinceMean !== null && (
        <p className="text-xs text-muted-foreground mb-3">
          Provincial regional mean: <span className="font-semibold">{Math.round(provinceMean)} min</span>
        </p>
      )}

      {mappingCoverage && mappingCoverage.total_hospitals > 0 && (
        <p
          className={clsx(
            "text-xs mb-3",
            mappingCoverage.coverage_percent < 60 ? "text-amber-700" : "text-muted-foreground"
          )}
        >
          Mapping coverage:{" "}
          <span className="font-semibold">
            {mappingCoverage.mapped_hospitals}/{mappingCoverage.total_hospitals}
          </span>{" "}
          hospitals ({mappingCoverage.coverage_percent.toFixed(1)}%)
          {mappingCoverage.coverage_percent < 60 && " — regional metrics may be incomplete."}
        </p>
      )}

      {loading ? (
        <div className="text-sm text-muted-foreground">Loading regional analytics...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {regions.map((region) => {
            const isSelected = selectedRegionId === region.region_id;
            return (
              <button
                key={region.region_id}
                type="button"
                onClick={() =>
                  onSelectRegion(isSelected ? null : region.region_id)
                }
                className={clsx(
                  "text-left rounded-lg border p-3 transition-all",
                  quartileClasses(region.quartile),
                  isSelected && "ring-2 ring-primary/40"
                )}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">
                      {region.region_code}
                    </p>
                    <p className="text-sm font-semibold text-foreground">{region.region_name}</p>
                  </div>
                  <span
                    className={clsx(
                      "text-[11px] px-2 py-0.5 rounded-full border font-medium",
                      trendClasses(region.trend)
                    )}
                  >
                    {trendLabel(region.trend, region.trend_change_percent)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-muted-foreground">Mean</p>
                    <p className="font-semibold text-foreground">{formatWait(region.period_mean)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Median</p>
                    <p className="font-semibold text-foreground">{formatWait(region.period_median)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Best</p>
                    <p className="font-semibold text-emerald-700">{formatWait(region.best_wait)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Worst</p>
                    <p className="font-semibold text-red-700">{formatWait(region.worst_wait)}</p>
                  </div>
                </div>

                <p className="text-[11px] text-muted-foreground mt-2">
                  Reporting hospitals: {region.reporting_count}/{region.hospital_count}
                </p>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}

export type { RegionAnalyticsRow };
