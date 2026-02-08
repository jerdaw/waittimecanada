'use client';

import { useEffect, useMemo, useState } from 'react';
import { MapPin, DollarSign, Navigation, AlertTriangle } from 'lucide-react';
import { Hospital } from '@/app/api/hospitals/route';
import { calculateDistance } from '@/utils/distance';

interface AccessInsightsSummaryProps {
  hospitals: Hospital[];
  userLocation: { lat: number; lon: number } | null;
  province: string;
}

type EquitySummaryStatus = 'ready' | 'no_reporting_data' | 'not_available_yet';

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
  QC: 1.60,
  AB: 1.45,
  BC: 1.75,
};

const FUEL_CONSUMPTION = 10; // L/100km
const AVG_PARKING = 15; // Mid-range estimate

function StatCard({ title, value, subtitle, icon, className = "" }: {
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
      {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
    </div>
  );
}

export function AccessInsightsSummary({
  hospitals,
  userLocation,
  province,
}: AccessInsightsSummaryProps) {
  const [equitySummary, setEquitySummary] = useState<EquitySummarySnapshot | null>(null);
  const [equityLoading, setEquityLoading] = useState(true);
  const [equityError, setEquityError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadEquitySummary() {
      setEquityLoading(true);
      setEquityError(null);

      try {
        const response = await fetch(`/api/analytics/equity-summary?province=${province}&period=7d`);
        const payload = await response.json();

        if (cancelled) return;
        if (response.ok && payload.success && payload.data) {
          setEquitySummary(payload.data as EquitySummarySnapshot);
        } else {
          setEquitySummary(null);
          setEquityError(payload.error ?? 'Failed to load equity linkage summary');
        }
      } catch {
        if (cancelled) return;
        setEquitySummary(null);
        setEquityError('Failed to load equity linkage summary');
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
          hospital.longitude
        );

        const gasPrice = GAS_PRICES[province] || 1.55;
        const roundTripKm = distance * 2;
        const fuelCost = (roundTripKm * FUEL_CONSUMPTION / 100) * gasPrice;
        const totalCost = fuelCost + AVG_PARKING;

        return {
          ...hospital,
          distance,
          accessCost: totalCost,
        };
      })
      .sort((a, b) => a.distance - b.distance);
  }, [hospitals, province, userLocation]);

  const within30km = hospitalsWithMetrics.filter((hospital) => hospital.distance <= 30);
  const within50km = hospitalsWithMetrics.filter((hospital) => hospital.distance <= 50);
  const avgAccessCost =
    within30km.length > 0
      ? within30km.reduce((sum, hospital) => sum + hospital.accessCost, 0) / within30km.length
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
              <strong>Logistical estimates only.</strong> Never delay care for cost. Call 911 for emergencies.
            </p>
          </div>

          {hospitalsWithMetrics.length > 0 ? (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard
                  title="ERs Within 30km"
                  value={within30km.length}
                  subtitle={`of ${hospitals.length} total`}
                  icon={<MapPin className="w-5 h-5" />}
                />

                <StatCard
                  title="Avg Access Cost"
                  value={`$${Math.round(avgAccessCost)}`}
                  subtitle="Fuel + Parking (30km radius)"
                  icon={<DollarSign className="w-5 h-5" />}
                />

                <StatCard
                  title="Nearest ER"
                  value={`${nearest.distance.toFixed(1)}km`}
                  subtitle={nearest.name}
                  icon={<Navigation className="w-5 h-5" />}
                />
              </div>

              {/* Additional Context */}
              {within30km.length === 0 && within50km.length > 0 && (
                <div className="p-3 bg-muted/50 border border-border rounded-lg">
                  <p className="text-xs text-muted-foreground">
                    <strong>Note:</strong> No emergency rooms within 30km. The nearest ER is{' '}
                    {nearest.distance.toFixed(1)}km away in {nearest.city}.
                  </p>
                </div>
              )}

              {/* Distribution insight */}
              {within30km.length > 0 && (
                <div className="p-3 bg-muted/50 border border-border rounded-lg">
                  <p className="text-xs text-muted-foreground">
                    Access costs range from <strong>${Math.round(nearest.accessCost)}</strong>{' '}
                    (nearest) to{' '}
                    <strong>${Math.round(within30km[within30km.length - 1].accessCost)}</strong>{' '}
                    (furthest within 30km). Costs include fuel ($
                    {(GAS_PRICES[province] || 1.55).toFixed(2)}/L in {province}) and parking.
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="p-6 text-center bg-card border border-border rounded-lg">
              <MapPin className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
              <p className="text-sm font-medium text-muted-foreground">
                No hospitals available to calculate access insights
              </p>
            </div>
          )}
        </>
      ) : (
        <div className="p-6 text-center bg-card border border-border rounded-lg">
          <MapPin className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
          <p className="text-sm font-medium text-muted-foreground">
            Enable location access to see personal access insights
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            We&apos;ll show you how many ERs are nearby and estimated travel costs
          </p>
        </div>
      )}

      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold text-foreground">Equity Access Snapshot (7d)</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          Tract-level linkage of low-income areas (income quintiles 1-2) and nearby reporting ER wait times.
        </p>

        {equityLoading ? (
          <p className="mt-3 text-sm text-muted-foreground">Loading equity linkage summary...</p>
        ) : equityError ? (
          <p className="mt-3 text-sm text-muted-foreground">{equityError}</p>
        ) : !equitySummary ? (
          <p className="mt-3 text-sm text-muted-foreground">No equity linkage summary available.</p>
        ) : equitySummary.status === 'not_available_yet' ? (
          <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-medium">Equity linkage summary not available yet</p>
            <p className="mt-1">{equitySummary.message}</p>
            {Array.isArray(equitySummary.setup_steps) && equitySummary.setup_steps.length > 0 && (
              <div className="mt-2 space-y-1 text-xs">
                {equitySummary.setup_steps.map((step) => (
                  <p key={step}>{step}</p>
                ))}
              </div>
            )}
          </div>
        ) : equitySummary.status === 'no_reporting_data' ? (
          <div className="mt-3 rounded-lg border border-border/60 bg-muted/30 p-3 text-sm text-muted-foreground">
            {equitySummary.message}
          </div>
        ) : (
          <div className="mt-3 space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <StatCard
                title="Low-Income Tracts"
                value={equitySummary.low_income_tracts ?? 0}
                subtitle={`of ${equitySummary.total_tracts ?? 0} tracts`}
                icon={<MapPin className="w-5 h-5" />}
              />
              <StatCard
                title="Hospitals Near Tracts"
                value={equitySummary.hospitals_near_low_income ?? 0}
                subtitle={`within ${equitySummary.threshold_km ?? 30}km`}
                icon={<Navigation className="w-5 h-5" />}
              />
              <StatCard
                title="Wait Gap vs Province"
                value={
                  equitySummary.wait_gap_minutes === null || equitySummary.wait_gap_minutes === undefined
                    ? "n/a"
                    : `${equitySummary.wait_gap_minutes > 0 ? "+" : ""}${Math.round(
                        equitySummary.wait_gap_minutes
                      )} min`
                }
                subtitle={`Reporting hospitals: ${equitySummary.reporting_hospitals ?? 0}`}
                icon={<AlertTriangle className="w-5 h-5" />}
              />
            </div>

            <p className="text-xs text-muted-foreground">
              Near-tract mean wait:{' '}
              <strong>
                {equitySummary.near_low_income_avg_wait === null ||
                equitySummary.near_low_income_avg_wait === undefined
                  ? "n/a"
                  : `${Math.round(equitySummary.near_low_income_avg_wait)} min`}
              </strong>{' '}
              • Province mean wait:{' '}
              <strong>
                {equitySummary.province_avg_wait === null || equitySummary.province_avg_wait === undefined
                  ? "n/a"
                  : `${Math.round(equitySummary.province_avg_wait)} min`}
              </strong>
            </p>

            {equitySummary.is_placeholder && (
              <p className="text-xs text-amber-700">
                Placeholder tract dataset in use. Replace with StatsCan-linked tract data before making policy conclusions.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
