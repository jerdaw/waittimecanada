"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { SystemTrendChart } from "@/components/SystemTrendChart";
import { RegionDashboard } from "@/components/RegionDashboard";

type TrendDirection = "improving" | "stable" | "worsening";

interface RegionRow {
  region_id: string;
  region_name: string;
  region_code: string;
  hospital_count: number;
  reporting_count: number;
  period_mean: number | null;
  period_median: number | null;
  best_wait: number | null;
  worst_wait: number | null;
  trend: TrendDirection;
  trend_change_percent: number;
  hospital_ids: string[];
  percentile: number | null;
  quartile: 1 | 2 | 3 | 4 | null;
}

interface BenchmarkRow {
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

interface RegionMappingCoverage {
  mapped_hospitals: number;
  total_hospitals: number;
  coverage_percent: number;
}

type OccupancyStatus = "available" | "no_reporting_data" | "not_available_yet";

interface OccupancySnapshot {
  province: string;
  available: boolean;
  status: OccupancyStatus;
  generated_at: string;
  message: string;
  fields: {
    patients_waiting: boolean;
    patients_in_treatment: boolean;
  };
  setup_steps?: string[];
  observations_24h?: number;
  hospitals_reporting?: number;
  averages?: {
    patients_waiting: number | null;
    patients_in_treatment: number | null;
  };
  latest_observation?: string | null;
}

const PROVINCE_OPTIONS = [
  { code: "ON", label: "Ontario" },
  { code: "QC", label: "Quebec" },
  { code: "AB", label: "Alberta" },
  { code: "BC", label: "British Columbia" },
];

function quartileLabel(quartile: number): string {
  if (quartile === 1) return "Q1";
  if (quartile === 2) return "Q2";
  if (quartile === 3) return "Q3";
  return "Q4";
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

function trendLabel(trend: TrendDirection): string {
  if (trend === "improving") return "Improving";
  if (trend === "worsening") return "Worsening";
  return "Stable";
}

export default function AnalyticsPage() {
  const [province, setProvince] = useState("ON");
  const [regions, setRegions] = useState<RegionRow[]>([]);
  const [provinceRegionMean, setProvinceRegionMean] = useState<number | null>(
    null,
  );
  const [regionMappingCoverage, setRegionMappingCoverage] =
    useState<RegionMappingCoverage | null>(null);
  const [regionSetupMessage, setRegionSetupMessage] = useState<string | null>(
    null,
  );
  const [regionSetupSteps, setRegionSetupSteps] = useState<string[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkRow[]>([]);
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [loadingRegions, setLoadingRegions] = useState(true);
  const [loadingBenchmarks, setLoadingBenchmarks] = useState(true);
  const [loadingOccupancy, setLoadingOccupancy] = useState(true);
  const [occupancy, setOccupancy] = useState<OccupancySnapshot | null>(null);

  useEffect(() => {
    let mounted = true;
    setSelectedRegionId(null);

    async function loadRegions() {
      setLoadingRegions(true);
      setRegionSetupMessage(null);
      setRegionSetupSteps([]);
      try {
        const response = await fetch(
          `/api/analytics/regions?province=${province}&period=7d`,
        );
        const json = await response.json();

        if (!mounted) return;
        if (response.ok && json.success && json.data) {
          setRegions(json.data.regions ?? []);
          setProvinceRegionMean(
            json.data.province_mean === null
              ? null
              : Number(json.data.province_mean),
          );
          if (json.data.mapping_coverage) {
            setRegionMappingCoverage({
              mapped_hospitals: Number(
                json.data.mapping_coverage.mapped_hospitals ?? 0,
              ),
              total_hospitals: Number(
                json.data.mapping_coverage.total_hospitals ?? 0,
              ),
              coverage_percent: Number(
                json.data.mapping_coverage.coverage_percent ?? 0,
              ),
            });
          } else {
            setRegionMappingCoverage(null);
          }
          setRegionSetupMessage(null);
          setRegionSetupSteps([]);
        } else if (json?.setup_required) {
          setRegions([]);
          setProvinceRegionMean(null);
          setRegionMappingCoverage(null);
          setRegionSetupMessage(
            String(
              json.message ??
                "Regional analytics requires schema initialization before it can be computed.",
            ),
          );
          setRegionSetupSteps(
            Array.isArray(json.setup_steps)
              ? json.setup_steps.map((step: unknown) => String(step))
              : [],
          );
        } else {
          setRegions([]);
          setProvinceRegionMean(null);
          setRegionMappingCoverage(null);
          setRegionSetupMessage(null);
          setRegionSetupSteps([]);
        }
      } catch {
        if (!mounted) return;
        setRegions([]);
        setProvinceRegionMean(null);
        setRegionMappingCoverage(null);
        setRegionSetupMessage(null);
        setRegionSetupSteps([]);
      } finally {
        if (mounted) {
          setLoadingRegions(false);
        }
      }
    }

    async function loadBenchmarks() {
      setLoadingBenchmarks(true);
      try {
        const response = await fetch(
          `/api/analytics/benchmarks?province=${province}&period=7d`,
        );
        const json = await response.json();

        if (!mounted) return;
        if (response.ok && json.success && json.data) {
          setBenchmarks(json.data.hospitals ?? []);
        } else {
          setBenchmarks([]);
        }
      } catch {
        if (!mounted) return;
        setBenchmarks([]);
      } finally {
        if (mounted) {
          setLoadingBenchmarks(false);
        }
      }
    }

    async function loadOccupancy() {
      setLoadingOccupancy(true);
      try {
        const response = await fetch(
          `/api/analytics/occupancy?province=${province}`,
        );
        const json = await response.json();

        if (!mounted) return;
        if (response.ok && json.success && json.data) {
          setOccupancy(json.data as OccupancySnapshot);
        } else {
          setOccupancy(null);
        }
      } catch {
        if (!mounted) return;
        setOccupancy(null);
      } finally {
        if (mounted) {
          setLoadingOccupancy(false);
        }
      }
    }

    loadRegions();
    loadBenchmarks();
    loadOccupancy();

    return () => {
      mounted = false;
    };
  }, [province]);

  const selectedRegionHospitalIds = useMemo(() => {
    if (!selectedRegionId) return null;
    const selectedRegion = regions.find(
      (region) => region.region_id === selectedRegionId,
    );
    if (!selectedRegion) return null;
    return new Set(selectedRegion.hospital_ids);
  }, [regions, selectedRegionId]);

  const filteredBenchmarks = useMemo(() => {
    if (!selectedRegionHospitalIds) return benchmarks;
    return benchmarks.filter((row) =>
      selectedRegionHospitalIds.has(row.hospital_id),
    );
  }, [benchmarks, selectedRegionHospitalIds]);

  const datasetSchema = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: "WaitTime Canada Analytics Dashboard",
    description:
      "Province-level emergency wait-time trends, regional benchmarking, and hospital peer rankings generated from standardized Canadian ER data.",
    creator: {
      "@type": "Organization",
      name: "WaitTime Canada",
    },
    variableMeasured: [
      "province_mean_wait_minutes",
      "region_mean_wait_minutes",
      "hospital_percentile_rank",
      "trend_change_percent",
    ],
    url: "https://waittimecanada.ca/analytics",
  };

  return (
    <main className="min-h-screen bg-muted/20">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />

      <Header />

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <section className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <Link href="/" className="text-sm text-primary hover:underline">
              Back to live map
            </Link>
            <h1 className="text-3xl font-bold text-foreground mt-2">
              Analytics Dashboard
            </h1>
            <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
              System-level wait-time trends, Ontario-style regional
              intelligence, and peer hospital ranking outputs for operational
              and research interpretation.
            </p>
          </div>

          <label className="inline-flex items-center gap-2 text-sm text-muted-foreground">
            Province
            <select
              className="rounded-md border border-border bg-background px-2.5 py-1.5 text-foreground"
              value={province}
              onChange={(event) => setProvince(event.target.value)}
            >
              {PROVINCE_OPTIONS.map((option) => (
                <option key={option.code} value={option.code}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </section>

        <SystemTrendChart province={province} />

        <section>
          <h2 className="text-lg font-semibold text-foreground mb-3">
            Regional Overview
          </h2>
          {regionSetupMessage && (
            <div className="mb-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
              <p className="font-medium">Regional analytics setup needed</p>
              <p className="mt-1">{regionSetupMessage}</p>
              {regionSetupSteps.length > 0 && (
                <div className="mt-2 space-y-1 font-mono text-xs">
                  {regionSetupSteps.map((step) => (
                    <p key={step}>{step}</p>
                  ))}
                </div>
              )}
            </div>
          )}
          <RegionDashboard
            province={province}
            period="7d"
            regions={regions}
            provinceMean={provinceRegionMean}
            mappingCoverage={regionMappingCoverage}
            loading={loadingRegions}
            selectedRegionId={selectedRegionId}
            onSelectRegion={setSelectedRegionId}
          />
        </section>

        <section className="rounded-xl border border-border/50 bg-card p-4">
          <h2 className="text-lg font-semibold text-foreground">
            Occupancy Signals
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Patients waiting and patients in treatment metrics are surfaced only
            when source fields are available and explicitly reported.
          </p>

          {loadingOccupancy ? (
            <p className="mt-3 text-sm text-muted-foreground">
              Loading occupancy status...
            </p>
          ) : !occupancy ? (
            <p className="mt-3 text-sm text-muted-foreground">
              Occupancy status could not be loaded at this time.
            </p>
          ) : occupancy.status === "not_available_yet" ? (
            <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
              <p className="font-medium">Occupancy metrics not available yet</p>
              <p className="mt-1">{occupancy.message}</p>
              {Array.isArray(occupancy.setup_steps) &&
                occupancy.setup_steps.length > 0 && (
                  <div className="mt-2 space-y-1 text-xs">
                    {occupancy.setup_steps.map((step) => (
                      <p key={step}>{step}</p>
                    ))}
                  </div>
                )}
            </div>
          ) : occupancy.status === "no_reporting_data" ? (
            <div className="mt-3 rounded-lg border border-border/60 bg-muted/30 p-3 text-sm text-muted-foreground">
              {occupancy.message}
            </div>
          ) : (
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-border/60 bg-background p-3">
                <p className="text-xs text-muted-foreground">
                  Avg Patients Waiting (24h)
                </p>
                <p className="mt-1 text-2xl font-semibold text-foreground tabular-nums">
                  {occupancy.averages?.patients_waiting === null ||
                  occupancy.averages?.patients_waiting === undefined
                    ? "n/a"
                    : Math.round(occupancy.averages.patients_waiting)}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Hospitals reporting: {occupancy.hospitals_reporting ?? 0}
                </p>
              </div>
              <div className="rounded-lg border border-border/60 bg-background p-3">
                <p className="text-xs text-muted-foreground">
                  Avg Patients In Treatment (24h)
                </p>
                <p className="mt-1 text-2xl font-semibold text-foreground tabular-nums">
                  {occupancy.averages?.patients_in_treatment === null ||
                  occupancy.averages?.patients_in_treatment === undefined
                    ? "n/a"
                    : Math.round(occupancy.averages.patients_in_treatment)}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Observations: {occupancy.observations_24h ?? 0}
                </p>
              </div>
              {occupancy.latest_observation && (
                <p className="text-xs text-muted-foreground sm:col-span-2">
                  Latest occupancy observation:{" "}
                  {new Date(occupancy.latest_observation).toLocaleString()}
                </p>
              )}
            </div>
          )}
        </section>

        <section className="rounded-xl border border-border/50 bg-card p-4">
          <div className="flex items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                Hospital Rankings
              </h2>
              <p className="text-xs text-muted-foreground">
                Seven-day peer ranking by average wait time within {province}
              </p>
            </div>
            {selectedRegionId && (
              <span className="text-xs text-primary">Region filter active</span>
            )}
          </div>

          {loadingBenchmarks ? (
            <div className="text-sm text-muted-foreground">
              Loading benchmark rankings...
            </div>
          ) : filteredBenchmarks.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No benchmark rows available.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b border-border/60 text-muted-foreground">
                    <th className="py-2 pr-2 font-medium">Hospital</th>
                    <th className="py-2 pr-2 font-medium">City</th>
                    <th className="py-2 pr-2 font-medium">7d Mean</th>
                    <th className="py-2 pr-2 font-medium">Percentile</th>
                    <th className="py-2 pr-2 font-medium">Quartile</th>
                    <th className="py-2 pr-2 font-medium">Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBenchmarks.map((row) => (
                    <tr
                      key={row.hospital_id}
                      className="border-b border-border/40"
                    >
                      <td className="py-2 pr-2 font-medium text-foreground">
                        {row.hospital_name}
                      </td>
                      <td className="py-2 pr-2 text-muted-foreground">
                        {row.city}
                      </td>
                      <td className="py-2 pr-2 tabular-nums">
                        {Math.round(row.period_mean)} min
                      </td>
                      <td className="py-2 pr-2 tabular-nums">
                        {formatOrdinal(row.percentile)}
                      </td>
                      <td className="py-2 pr-2">
                        {quartileLabel(row.quartile)}
                      </td>
                      <td className="py-2 pr-2">
                        {trendLabel(row.trend)} (
                        {Math.abs(row.trend_change_percent).toFixed(1)}%)
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
