"use client";

import { useEffect, useMemo, useState } from "react";
import { MapPin, DollarSign, Navigation, AlertTriangle } from "lucide-react";
import { Hospital } from "@/app/api/hospitals/route";
import { calculateDistance } from "@/utils/distance";
import { useTranslations } from "next-intl";

interface AccessInsightsSummaryProps {
  hospitals: Hospital[];
  userLocation: { lat: number; lon: number } | null;
  province: string;
}

type EquitySummaryStatus = "ready" | "no_reporting_data" | "not_available_yet";

interface EquitySummarySnapshot {
  province: string;
  period: string;
  status: EquitySummaryStatus;
  generated_at: string;
  is_placeholder: boolean;
  message: string;
  low_income_tracts?: number;
  total_tracts?: number;
  reporting_hospitals?: number;
  hospitals_near_low_income?: number;
  province_avg_wait?: number | null;
  near_low_income_avg_wait?: number | null;
  wait_gap_minutes?: number | null;
  threshold_km?: number;
  setup_steps?: string[];
}

// Gas prices from AccessBurdenEstimator
const GAS_PRICES: Record<string, number> = {
  ON: 1.55,
  QC: 1.6,
  AB: 1.45,
  BC: 1.75,
};

const FUEL_CONSUMPTION = 10; // L/100km
const AVG_PARKING = 15; // Mid-range estimate

function StatCard({
  title,
  value,
  subtitle,
  icon,
  className = "",
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`p-4 rounded-lg border border-border bg-card ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        <div className="text-muted-foreground">{icon}</div>
      </div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
      {subtitle && (
        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
      )}
    </div>
  );
}

export function AccessInsightsSummary({
  hospitals,
  userLocation,
  province,
}: AccessInsightsSummaryProps) {
  const t = useTranslations('AccessInsights');
  const [equitySummary, setEquitySummary] =
    useState<EquitySummarySnapshot | null>(null);
  const [equityLoading, setEquityLoading] = useState(true);
  const [equityError, setEquityError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadEquitySummary() {
      setEquityLoading(true);
      setEquityError(null);

      try {
        const response = await fetch(
          `/api/analytics/equity-summary?province=${province}&period=7d`,
        );
        const payload = await response.json();

        if (cancelled) return;
        if (response.ok && payload.success && payload.data) {
          setEquitySummary(payload.data as EquitySummarySnapshot);
        } else {
          setEquitySummary(null);
          setEquityError(
            payload.error ?? "Failed to load equity linkage summary",
          );
        }
      } catch {
        if (cancelled) return;
        setEquitySummary(null);
        setEquityError("Failed to load equity linkage summary");
      } finally {
        if (!cancelled) {
          setEquityLoading(false);
        }
      }
    }

    loadEquitySummary();
    return () => {
      cancelled = true;
    };
  }, [province]);

  const hospitalsWithMetrics = useMemo(() => {
    if (!userLocation) return [];

    return hospitals
      .map((hospital) => {
        const distance = calculateDistance(
          userLocation.lat,
          userLocation.lon,
          hospital.latitude,
          hospital.longitude,
        );

        const gasPrice = GAS_PRICES[province] || 1.55;
        const roundTripKm = distance * 2;
        const fuelCost = ((roundTripKm * FUEL_CONSUMPTION) / 100) * gasPrice;
        const totalCost = fuelCost + AVG_PARKING;

        return {
          ...hospital,
          distance,
          accessCost: totalCost,
        };
      })
      .sort((a, b) => a.distance - b.distance);
  }, [hospitals, province, userLocation]);

  const within30km = hospitalsWithMetrics.filter(
    (hospital) => hospital.distance <= 30,
  );
  const within50km = hospitalsWithMetrics.filter(
    (hospital) => hospital.distance <= 50,
  );
  const avgAccessCost =
    within30km.length > 0
      ? within30km.reduce((sum, hospital) => sum + hospital.accessCost, 0) /
        within30km.length
      : 0;
  const nearest = hospitalsWithMetrics[0];

  return (
    <div className="space-y-4">
      {userLocation ? (
        <>
          {/* Disclaimer */}
          <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-amber-800 dark:text-amber-200">
              {t('disclaimer')}
            </p>
          </div>

          {hospitalsWithMetrics.length > 0 ? (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard
                  title={t('stats.erWithin30km')}
                  value={within30km.length}
                  subtitle={t('stats.totalHospitals', {total: hospitals.length})}
                  icon={<MapPin className="w-5 h-5" />}
                />

                <StatCard
                  title={t('stats.avgCost')}
                  value={`$${Math.round(avgAccessCost)}`}
                  subtitle={t('stats.costDesc')}
                  icon={<DollarSign className="w-5 h-5" />}
                />

                <StatCard
                  title={t('stats.nearestEr')}
                  value={`${nearest.distance.toFixed(1)}km`}
                  subtitle={nearest.name}
                  icon={<Navigation className="w-5 h-5" />}
                />
              </div>

              {/* Additional Context */}
              {within30km.length === 0 && within50km.length > 0 && (
                <div className="p-3 bg-muted/50 border border-border rounded-lg">
                  <p className="text-xs text-muted-foreground">
                    {t('noErNearby', {distance: nearest.distance.toFixed(1), city: nearest.city})}
                  </p>
                </div>
              )}

              {/* Distribution insight */}
              {within30km.length > 0 && (
                <div className="p-3 bg-muted/50 border border-border rounded-lg">
                  <p className="text-xs text-muted-foreground">
                    {t('costRange', {
                      min: Math.round(nearest.accessCost),
                      max: Math.round(within30km[within30km.length - 1].accessCost),
                      price: (GAS_PRICES[province] || 1.55).toFixed(2),
                      province: province
                    })}
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="p-6 text-center bg-card border border-border rounded-lg">
              <MapPin className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
              <p className="text-sm font-medium text-muted-foreground">
                {t('noHospitals')}
              </p>
            </div>
          )}
        </>
      ) : (
        <div className="p-6 text-center bg-card border border-border rounded-lg">
          <MapPin className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
          <p className="text-sm font-medium text-muted-foreground">
            {t('enableLocation.title')}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {t('enableLocation.subtitle')}
          </p>
        </div>
      )}

      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold text-foreground">
          {t('equity.title')}
        </h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {t('equity.description')}
        </p>

        {equityLoading ? (
          <p className="mt-3 text-sm text-muted-foreground">
            {t('equity.loading')}
          </p>
        ) : equityError ? (
          <p className="mt-3 text-sm text-muted-foreground">{equityError}</p>
        ) : !equitySummary ? (
          <p className="mt-3 text-sm text-muted-foreground">
            {t('equity.unavailable')}
          </p>
        ) : equitySummary.status === "not_available_yet" ? (
          <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-medium">
              {t('equity.notReady')}
            </p>
            <p className="mt-1">{equitySummary.message}</p>
            {Array.isArray(equitySummary.setup_steps) &&
              equitySummary.setup_steps.length > 0 && (
                <div className="mt-2 space-y-1 text-xs">
                  {equitySummary.setup_steps.map((step) => (
                    <p key={step}>{step}</p>
                  ))}
                </div>
              )}
          </div>
        ) : equitySummary.status === "no_reporting_data" ? (
          <div className="mt-3 rounded-lg border border-border/60 bg-muted/30 p-3 text-sm text-muted-foreground">
            {equitySummary.message}
          </div>
        ) : (
          <div className="mt-3 space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <StatCard
                title={t('equity.lowIncomeTracts')}
                value={equitySummary.low_income_tracts ?? 0}
                subtitle={t('equity.tractsCount', {total: equitySummary.total_tracts ?? 0})}
                icon={<MapPin className="w-5 h-5" />}
              />
              <StatCard
                title={t('equity.hospitalsNear')}
                value={equitySummary.hospitals_near_low_income ?? 0}
                subtitle={t('equity.withinKm', {distance: equitySummary.threshold_km ?? 30})}
                icon={<Navigation className="w-5 h-5" />}
              />
              <StatCard
                title={t('equity.waitGap')}
                value={
                  equitySummary.wait_gap_minutes === null ||
                  equitySummary.wait_gap_minutes === undefined
                    ? "n/a"
                    : `${equitySummary.wait_gap_minutes > 0 ? "+" : ""}${Math.round(
                        equitySummary.wait_gap_minutes,
                      )} min`
                }
                subtitle={t('equity.reportingCount', {count: equitySummary.reporting_hospitals ?? 0})}
                icon={<AlertTriangle className="w-5 h-5" />}
              />
            </div>

            <p className="text-xs text-muted-foreground">
              {t('equity.nearTractMean')}{" "}
              <strong>
                {equitySummary.near_low_income_avg_wait === null ||
                equitySummary.near_low_income_avg_wait === undefined
                  ? "n/a"
                  : `${Math.round(equitySummary.near_low_income_avg_wait)} min`}
              </strong>{" "}
              • {t('equity.provinceMean')}{" "}
              <strong>
                {equitySummary.province_avg_wait === null ||
                equitySummary.province_avg_wait === undefined
                  ? "n/a"
                  : `${Math.round(equitySummary.province_avg_wait)} min`}
              </strong>
            </p>

            {equitySummary.is_placeholder && (
              <p className="text-xs text-amber-700">
                {t('equity.placeholder')}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
