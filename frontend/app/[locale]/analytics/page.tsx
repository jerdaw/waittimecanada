"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { SystemTrendChart } from "@/components/SystemTrendChart";
import { RegionDashboard } from "@/components/RegionDashboard";
import { useTranslations } from "next-intl";

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
  metric_family: string;
  start_event: string;
  end_event: string;
  statistic_type: string;
}

interface MethodologySummary {
  is_homogeneous: boolean;
  distinct_groups: number;
  divergence_note: string | null;
  groups: any[];
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
  occupancy_percentage?: {
    hospitals_reporting: number;
    average: number | null;
    min: number | null;
    max: number | null;
    note: string;
  };
}

const PROVINCE_CODES = ["ON", "QC", "AB", "BC"] as const;

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

export default function AnalyticsPage() {
  const t = useTranslations("AnalyticsPage");
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
  const [methodologySummary, setMethodologySummary] =
    useState<MethodologySummary | null>(null);
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
          setMethodologySummary(json.data.methodology_summary ?? null);
        } else {
          setBenchmarks([]);
          setMethodologySummary(null);
        }
      } catch {
        if (!mounted) return;
        setBenchmarks([]);
        setMethodologySummary(null);
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
    name: "Wait Time Canada Analytics Dashboard",
    description:
      "Province-level emergency wait-time trends, regional benchmarking, and hospital peer rankings generated from standardized Canadian ER data.",
    creator: {
      "@type": "Organization",
      name: "Wait Time Canada",
    },
    variableMeasured: [
      "province_mean_wait_minutes",
      "region_mean_wait_minutes",
      "hospital_percentile_rank",
      "trend_change_percent",
    ],
    url: "https://wait-time.ca/analytics",
  };

  return (
    <main className="min-h-screen bg-muted/20 flex flex-col">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />

      <Header />

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 flex-1">
        <section className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <Link href="/" className="text-sm text-primary hover:underline">
              {t("backToMap")}
            </Link>
            <h1 className="text-3xl font-bold text-foreground mt-2">
              {t("title")}
            </h1>
            <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
              {t("subtitle")}
            </p>
          </div>

          <label className="inline-flex items-center gap-2 text-sm text-muted-foreground">
            {t("province")}
            <select
              className="rounded-md border border-border bg-background px-2.5 py-1.5 text-foreground"
              value={province}
              onChange={(event) => setProvince(event.target.value)}
            >
              {PROVINCE_CODES.map((code) => (
                <option key={code} value={code}>
                  {t(`provinces.${code}`)}
                </option>
              ))}
            </select>
          </label>
        </section>

        <SystemTrendChart province={province} />

        <section>
          <h2 className="text-xl font-semibold text-foreground mb-3">
            {t("regionalOverview")}
          </h2>
          {regionSetupMessage && (
            <div className="mb-3 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700 p-3 text-sm text-amber-900 dark:text-amber-200">
              <p className="font-medium">{t("regionSetupNeeded")}</p>
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

        <section className="rounded-xl border border-border/50 bg-card p-5">
          <h2 className="text-xl font-semibold text-foreground">
            {t("occupancy.title")}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("occupancy.subtitle")}
          </p>

          {loadingOccupancy ? (
            <p className="mt-3 text-sm text-muted-foreground">
              {t("occupancy.loading")}
            </p>
          ) : !occupancy ? (
            <p className="mt-3 text-sm text-muted-foreground">
              {t("occupancy.loadError")}
            </p>
          ) : occupancy.status === "not_available_yet" ? (
            <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700 p-3 text-sm text-amber-900 dark:text-amber-200">
              <p className="font-medium">{t("occupancy.notAvailable")}</p>
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
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-border/50 bg-background p-5">
                <p className="text-sm text-muted-foreground">
                  {t("occupancy.avgWaiting")}
                </p>
                <p className="mt-2 text-4xl font-bold text-foreground tabular-nums">
                  {occupancy.averages?.patients_waiting === null ||
                  occupancy.averages?.patients_waiting === undefined
                    ? t("occupancy.na")
                    : Math.round(occupancy.averages.patients_waiting)}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {t("occupancy.hospitalsReporting", {
                    count: occupancy.hospitals_reporting ?? 0,
                  })}
                </p>
              </div>
              <div className="rounded-xl border border-border/50 bg-background p-5">
                <p className="text-sm text-muted-foreground">
                  {t("occupancy.avgTreatment")}
                </p>
                <p className="mt-2 text-4xl font-bold text-foreground tabular-nums">
                  {occupancy.averages?.patients_in_treatment === null ||
                  occupancy.averages?.patients_in_treatment === undefined
                    ? t("occupancy.na")
                    : Math.round(occupancy.averages.patients_in_treatment)}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {t("occupancy.observations", {
                    count: occupancy.observations_24h ?? 0,
                  })}
                </p>
              </div>
              {occupancy.latest_observation && (
                <p className="text-xs text-muted-foreground sm:col-span-2">
                  {t("occupancy.latestObservation", {
                    time: new Date(
                      occupancy.latest_observation,
                    ).toLocaleString(),
                  })}
                </p>
              )}
            </div>
          )}
        </section>

        {occupancy?.status === "available" &&
          occupancy?.occupancy_percentage && (
            <details className="rounded-xl border border-border/50 bg-card group overflow-hidden">
              <summary className="p-4 font-semibold text-foreground cursor-pointer list-none flex justify-between items-center hover:bg-muted/30 transition-colors">
                {t("occupancyTrend")}
                <span className="text-muted-foreground group-open:rotate-180 transition-transform">
                  &#x25BC;
                </span>
              </summary>
              <div className="border-t border-border/50">
                <SystemTrendChart
                  province={province}
                  metricFamily="STRETCHER_OCCUPANCY"
                  className="p-4 bg-transparent"
                />
              </div>
            </details>
          )}

        <section className="rounded-xl border border-border/50 bg-card p-5">
          <div className="flex items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                {t("rankings.title")}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {t("rankings.subtitle", { province })}
              </p>
            </div>
            {selectedRegionId && (
              <span className="text-xs text-primary">
                {t("rankings.regionFilterActive")}
              </span>
            )}
          </div>

          {!loadingBenchmarks &&
            methodologySummary &&
            !methodologySummary.is_homogeneous && (
              <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700 p-3 text-sm text-amber-900 dark:text-amber-200">
                <p className="font-semibold flex items-center gap-2">
                  <span aria-hidden="true">&#x26A0;&#xFE0F;</span>{" "}
                  {t("rankings.methodologyDivergence")}
                </p>
                <p className="mt-1">{methodologySummary.divergence_note}</p>
                <div className="mt-2 text-xs">
                  <Link
                    href="/methods"
                    className="font-medium underline hover:text-amber-700 dark:hover:text-amber-300"
                  >
                    {t("rankings.viewMatrix")} &rarr;
                  </Link>
                </div>
              </div>
            )}

          {loadingBenchmarks ? (
            <div className="text-sm text-muted-foreground">
              {t("rankings.loading")}
            </div>
          ) : filteredBenchmarks.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              {t("rankings.empty")}
            </div>
          ) : (
            <div className="overflow-x-auto -mx-5">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10 bg-card">
                  <tr className="text-left border-b-2 border-border/60 text-muted-foreground">
                    <th className="py-2.5 px-5 font-medium">
                      {t("rankings.columns.hospital")}
                    </th>
                    <th className="py-2.5 pr-3 font-medium">
                      {t("rankings.columns.city")}
                    </th>
                    <th className="py-2.5 pr-3 font-medium">
                      {t("rankings.columns.mean")}
                    </th>
                    <th className="py-2.5 pr-3 font-medium">
                      {t("rankings.columns.percentile")}
                    </th>
                    <th className="py-2.5 pr-3 font-medium">
                      {t("rankings.columns.quartile")}
                    </th>
                    <th className="py-2.5 pr-5 font-medium">
                      {t("rankings.columns.trend")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBenchmarks.map((row, idx) => (
                    <tr
                      key={row.hospital_id}
                      className={`border-b border-border/30 transition-colors hover:bg-muted/30 ${idx % 2 === 1 ? "bg-muted/10" : ""}`}
                    >
                      <td className="py-2.5 px-5 font-medium text-foreground">
                        <div>{row.hospital_name}</div>
                        <div className="mt-0.5">
                          <span className="inline-flex items-center rounded-sm bg-muted/50 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                            {row.statistic_type} / {row.start_event}&rarr;
                            {row.end_event}
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-3 text-muted-foreground">
                        {row.city}
                      </td>
                      <td className="py-2.5 pr-3 tabular-nums">
                        {Math.round(row.period_mean)} {t("rankings.min")}
                      </td>
                      <td className="py-2.5 pr-3 tabular-nums">
                        {formatOrdinal(row.percentile)}
                      </td>
                      <td className="py-2.5 pr-3">
                        {quartileLabel(row.quartile)}
                      </td>
                      <td className="py-2.5 pr-5">
                        {t(`trend.${row.trend}`)} (
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

      <Footer />
    </main>
  );
}
