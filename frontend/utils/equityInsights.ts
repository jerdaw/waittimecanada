import { calculateDistance } from "@/utils/distance";
import type { EquityFeature, EquityFeatureCollection } from "@/utils/equity";

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
  sensitivity_analysis: Array<{
    threshold_km: number;
    hospitals_near_low_income: number;
    near_low_income_avg_wait: number | null;
    wait_gap_minutes: number | null;
  }>;
  uncertainty: {
    method: "bootstrap_percentile";
    iterations: number;
    near_low_income_avg_wait_ci95: { lower: number | null; upper: number | null };
    wait_gap_minutes_ci95: { lower: number | null; upper: number | null };
  };
}

function average(values: number[]): number | null {
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function percentile(sortedValues: number[], percentileValue: number): number | null {
  if (!sortedValues.length) return null;
  if (sortedValues.length === 1) return sortedValues[0];
  const index = (sortedValues.length - 1) * percentileValue;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sortedValues[lower];
  const weight = index - lower;
  return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
}

function createDeterministicRng(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 2 ** 32;
  };
}

function bootstrapMeanCi95(
  values: number[],
  iterations: number,
  seed: number,
): { lower: number | null; upper: number | null } {
  if (values.length < 2) {
    return { lower: null, upper: null };
  }
  const rng = createDeterministicRng(seed);
  const means: number[] = [];
  for (let i = 0; i < iterations; i += 1) {
    const sample: number[] = [];
    for (let j = 0; j < values.length; j += 1) {
      sample.push(values[Math.floor(rng() * values.length)]);
    }
    const mean = average(sample);
    if (mean !== null) {
      means.push(mean);
    }
  }
  means.sort((a, b) => a - b);
  return {
    lower: percentile(means, 0.025),
    upper: percentile(means, 0.975),
  };
}

function bootstrapGapCi95(
  nearValues: number[],
  provinceValues: number[],
  iterations: number,
  seed: number,
): { lower: number | null; upper: number | null } {
  if (nearValues.length < 2 || provinceValues.length < 2) {
    return { lower: null, upper: null };
  }
  const rng = createDeterministicRng(seed);
  const diffs: number[] = [];
  for (let i = 0; i < iterations; i += 1) {
    const nearSample: number[] = [];
    const provinceSample: number[] = [];
    for (let j = 0; j < nearValues.length; j += 1) {
      nearSample.push(nearValues[Math.floor(rng() * nearValues.length)]);
    }
    for (let j = 0; j < provinceValues.length; j += 1) {
      provinceSample.push(provinceValues[Math.floor(rng() * provinceValues.length)]);
    }
    const nearMean = average(nearSample);
    const provinceMean = average(provinceSample);
    if (nearMean !== null && provinceMean !== null) {
      diffs.push(nearMean - provinceMean);
    }
  }
  diffs.sort((a, b) => a - b);
  return {
    lower: percentile(diffs, 0.025),
    upper: percentile(diffs, 0.975),
  };
}

function polygonCentroid(
  feature: EquityFeature,
): { lat: number; lon: number } | null {
  let ring: number[][] | undefined;
  if (feature.geometry.type === "Polygon") {
    ring = feature.geometry.coordinates[0];
  } else {
    ring = feature.geometry.coordinates[0]?.[0];
  }
  if (!Array.isArray(ring) || ring.length < 3) return null;

  // Ignore closing point duplicate if present.
  const points = ring.slice(0, -1);
  if (!points.length) return null;

  const totals = points.reduce(
    (acc, point) => ({
      lon: acc.lon + Number(point[0]),
      lat: acc.lat + Number(point[1]),
    }),
    { lon: 0, lat: 0 },
  );

  return {
    lon: totals.lon / points.length,
    lat: totals.lat / points.length,
  };
}

export function computeEquityLinkageSummary(
  hospitals: HospitalWaitPoint[],
  equityData: EquityFeatureCollection,
  thresholdKm = 30,
): EquityLinkageSummary {
  const bootstrapIterations = 1000;
  const defaultSensitivityThresholds = [10, 20, 30, 40];
  const lowIncomeCentroids = equityData.features
    .filter(
      (feature) =>
        feature.properties.income_quintile > 0 &&
        feature.properties.income_quintile <= 2,
    )
    .map((feature) => polygonCentroid(feature))
    .filter(
      (centroid): centroid is { lat: number; lon: number } => centroid !== null,
    );

  const reportingHospitals = hospitals.filter(
    (hospital) => hospital.period_mean !== null,
  );
  const reportingWaits = reportingHospitals
    .map((hospital) => hospital.period_mean)
    .filter((value): value is number => value !== null);

  const nearLowIncomeHospitalsAt = (distanceThresholdKm: number) =>
    reportingHospitals.filter((hospital) => {
      if (lowIncomeCentroids.length === 0) return false;
      return lowIncomeCentroids.some((centroid) => {
        const distanceKm = calculateDistance(
          hospital.latitude,
          hospital.longitude,
          centroid.lat,
          centroid.lon,
        );
        return distanceKm <= distanceThresholdKm;
      });
    });

  const nearLowIncomeHospitals = nearLowIncomeHospitalsAt(thresholdKm);
  const nearWaits = nearLowIncomeHospitals
    .map((hospital) => hospital.period_mean)
    .filter((value): value is number => value !== null);

  const provinceAvgWait = average(reportingWaits);
  const nearAvgWait = average(nearWaits);

  const sensitivityThresholds = Array.from(
    new Set([...defaultSensitivityThresholds, thresholdKm]),
  ).sort((a, b) => a - b);

  const sensitivityAnalysis = sensitivityThresholds.map((distanceThreshold) => {
    const nearbyHospitals = nearLowIncomeHospitalsAt(distanceThreshold);
    const nearbyWaits = nearbyHospitals
      .map((hospital) => hospital.period_mean)
      .filter((value): value is number => value !== null);
    const nearbyMean = average(nearbyWaits);
    return {
      threshold_km: distanceThreshold,
      hospitals_near_low_income: nearbyHospitals.length,
      near_low_income_avg_wait: nearbyMean,
      wait_gap_minutes:
        provinceAvgWait === null || nearbyMean === null
          ? null
          : nearbyMean - provinceAvgWait,
    };
  });

  const nearMeanCi95 = bootstrapMeanCi95(
    nearWaits,
    bootstrapIterations,
    nearWaits.length + 17,
  );
  const gapCi95 = bootstrapGapCi95(
    nearWaits,
    reportingWaits,
    bootstrapIterations,
    nearWaits.length + reportingWaits.length + 31,
  );

  return {
    low_income_tracts: lowIncomeCentroids.length,
    total_tracts: equityData.features.length,
    reporting_hospitals: reportingHospitals.length,
    hospitals_near_low_income: nearLowIncomeHospitals.length,
    province_avg_wait: provinceAvgWait,
    near_low_income_avg_wait: nearAvgWait,
    wait_gap_minutes:
      provinceAvgWait === null || nearAvgWait === null
        ? null
        : nearAvgWait - provinceAvgWait,
    threshold_km: thresholdKm,
    sensitivity_analysis: sensitivityAnalysis,
    uncertainty: {
      method: "bootstrap_percentile",
      iterations: bootstrapIterations,
      near_low_income_avg_wait_ci95: nearMeanCi95,
      wait_gap_minutes_ci95: gapCi95,
    },
  };
}

export function isDescriptiveEquityAssociation(): true {
  // Named helper for route metadata clarity.
  return true;
}
