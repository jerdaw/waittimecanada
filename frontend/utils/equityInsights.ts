import { calculateDistance } from "@/utils/distance";
import type { EquityFeatureCollection } from "@/utils/equity";

export interface HospitalWaitPoint {
  hospital_id: string;
  latitude: number;
  longitude: number;
  period_mean: number | null;
}

export interface EquityLinkageSummary {
  low_income_tracts: number;
  total_tracts: number;
  reporting_hospitals: number;
  hospitals_near_low_income: number;
  province_avg_wait: number | null;
  near_low_income_avg_wait: number | null;
  wait_gap_minutes: number | null;
  threshold_km: number;
}

function average(values: number[]): number | null {
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function polygonCentroid(coordinates: number[][][]): { lat: number; lon: number } | null {
  const ring = coordinates[0];
  if (!Array.isArray(ring) || ring.length < 3) return null;

  // Ignore closing point duplicate if present.
  const points = ring.slice(0, -1);
  if (!points.length) return null;

  const totals = points.reduce(
    (acc, point) => ({
      lon: acc.lon + Number(point[0]),
      lat: acc.lat + Number(point[1]),
    }),
    { lon: 0, lat: 0 }
  );

  return {
    lon: totals.lon / points.length,
    lat: totals.lat / points.length,
  };
}

export function computeEquityLinkageSummary(
  hospitals: HospitalWaitPoint[],
  equityData: EquityFeatureCollection,
  thresholdKm = 30
): EquityLinkageSummary {
  const lowIncomeCentroids = equityData.features
    .filter((feature) => feature.properties.income_quintile <= 2)
    .map((feature) => polygonCentroid(feature.geometry.coordinates))
    .filter((centroid): centroid is { lat: number; lon: number } => centroid !== null);

  const reportingHospitals = hospitals.filter((hospital) => hospital.period_mean !== null);
  const reportingWaits = reportingHospitals
    .map((hospital) => hospital.period_mean)
    .filter((value): value is number => value !== null);

  const nearLowIncomeHospitals = reportingHospitals.filter((hospital) => {
    if (lowIncomeCentroids.length === 0) return false;
    return lowIncomeCentroids.some((centroid) => {
      const distanceKm = calculateDistance(
        hospital.latitude,
        hospital.longitude,
        centroid.lat,
        centroid.lon
      );
      return distanceKm <= thresholdKm;
    });
  });

  const nearWaits = nearLowIncomeHospitals
    .map((hospital) => hospital.period_mean)
    .filter((value): value is number => value !== null);

  const provinceAvgWait = average(reportingWaits);
  const nearAvgWait = average(nearWaits);

  return {
    low_income_tracts: lowIncomeCentroids.length,
    total_tracts: equityData.features.length,
    reporting_hospitals: reportingHospitals.length,
    hospitals_near_low_income: nearLowIncomeHospitals.length,
    province_avg_wait: provinceAvgWait,
    near_low_income_avg_wait: nearAvgWait,
    wait_gap_minutes:
      provinceAvgWait === null || nearAvgWait === null ? null : nearAvgWait - provinceAvgWait,
    threshold_km: thresholdKm,
  };
}
