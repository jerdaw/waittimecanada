'use client';

import { MapPin, DollarSign, Navigation, AlertTriangle } from 'lucide-react';
import { Hospital } from '@/app/api/hospitals/route';
import { calculateDistance } from '@/utils/distance';

interface AccessInsightsSummaryProps {
  hospitals: Hospital[];
  userLocation: { lat: number; lon: number } | null;
  province: string;
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
  if (!userLocation) {
    return (
      <div className="p-6 text-center bg-card border border-border rounded-lg">
        <MapPin className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
        <p className="text-sm font-medium text-muted-foreground">
          Enable location access to see access insights
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          We&apos;ll show you how many ERs are nearby and estimated travel costs
        </p>
      </div>
    );
  }

  // Calculate distances and access costs for all hospitals
  const hospitalsWithMetrics = hospitals
    .map(h => {
      const distance = calculateDistance(
        userLocation.lat,
        userLocation.lon,
        h.latitude,
        h.longitude
      );

      const gasPrice = GAS_PRICES[province] || 1.55;
      const roundTripKm = distance * 2;
      const fuelCost = (roundTripKm * FUEL_CONSUMPTION / 100) * gasPrice;
      const totalCost = fuelCost + AVG_PARKING;

      return {
        ...h,
        distance,
        accessCost: totalCost,
      };
    })
    .sort((a, b) => a.distance - b.distance);

  if (hospitalsWithMetrics.length === 0) {
    return (
      <div className="p-6 text-center bg-card border border-border rounded-lg">
        <MapPin className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
        <p className="text-sm font-medium text-muted-foreground">
          No hospitals available to calculate access insights
        </p>
      </div>
    );
  }

  // Calculate statistics
  const within30km = hospitalsWithMetrics.filter(h => h.distance <= 30);
  const within50km = hospitalsWithMetrics.filter(h => h.distance <= 50);

  const avgAccessCost = within30km.length > 0
    ? within30km.reduce((sum, h) => sum + h.accessCost, 0) / within30km.length
    : 0;

  const nearest = hospitalsWithMetrics[0];

  return (
    <div className="space-y-4">
      {/* Disclaimer */}
      <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg">
        <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-amber-800 dark:text-amber-200">
          <strong>Logistical estimates only.</strong> Never delay care for cost. Call 911 for emergencies.
        </p>
      </div>

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
            <strong>Note:</strong> No emergency rooms within 30km. The nearest ER is {nearest.distance.toFixed(1)}km away in {nearest.city}.
          </p>
        </div>
      )}

      {/* Distribution insight */}
      {within30km.length > 0 && (
        <div className="p-3 bg-muted/50 border border-border rounded-lg">
          <p className="text-xs text-muted-foreground">
            Access costs range from <strong>${Math.round(nearest.accessCost)}</strong> (nearest)
            to <strong>${Math.round(within30km[within30km.length - 1].accessCost)}</strong> (furthest within 30km).
            Costs include fuel (${(GAS_PRICES[province] || 1.55).toFixed(2)}/L in {province}) and parking.
          </p>
        </div>
      )}
    </div>
  );
}
