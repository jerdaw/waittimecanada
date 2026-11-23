import { DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES } from "@/utils/live-scraper-sources";

/**
 * Classification of a hospital's TIME_TO_PROVIDER value.
 *
 * - `current`: a live-estimate source whose own latest measurement is recent.
 * - `stale`: a live-estimate source whose latest measurement is too old (or has
 *   an unusable timestamp). The value must not be shown as current.
 * - `monthly`: a source that publishes a monthly average (Ontario Health). The
 *   value is never current, whatever its age.
 * - `none`: no measurement at all.
 */
export type WaitTimeStatus = "current" | "stale" | "monthly" | "none";

/** Sources that publish a retrospective monthly average, not a live estimate. */
export const MONTHLY_SOURCE_IDS = ["ontario-health"] as const;

export const ONTARIO_HEALTH_SOURCE_URL =
  "https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments";

export const MONTHLY_SOURCE_URLS: Readonly<Record<string, string>> = {
  "ontario-health": ONTARIO_HEALTH_SOURCE_URL,
};

/**
 * Per-source freshness cutoffs for live-estimate sources, in minutes.
 *
 * Alberta, BC and Quebec are all collected hourly, so a hospital that is still
 * reporting has a measurement no older than about one collection interval. The
 * cutoff is two intervals, which is the existing heartbeat threshold: one missed
 * or late hourly run is tolerated, a second is not. A source id that is not
 * listed (including an unknown one) uses the same default, so an unrecognised
 * source fails closed rather than open.
 */
export const LIVE_ESTIMATE_STALE_THRESHOLD_MINUTES: Readonly<
  Record<string, number>
> = {
  "alberta-ahs": DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES,
  "bc-phsa": DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES,
  "quebec-msss": DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES,
};

export function isMonthlySource(sourceId: unknown): boolean {
  return (
    typeof sourceId === "string" &&
    (MONTHLY_SOURCE_IDS as readonly string[]).includes(sourceId)
  );
}

export function getMonthlySourceUrl(sourceId: unknown): string | undefined {
  return typeof sourceId === "string"
    ? MONTHLY_SOURCE_URLS[sourceId]
    : undefined;
}

/** Cutoff for a live-estimate source; unknown sources get the default. */
export function getLiveEstimateStaleThresholdMinutes(
  sourceId: unknown,
): number {
  return (
    (typeof sourceId === "string"
      ? LIVE_ESTIMATE_STALE_THRESHOLD_MINUTES[sourceId]
      : undefined) ?? DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES
  );
}

/**
 * True when `timestamp` is no older than `thresholdMinutes`. The boundary is
 * inclusive (age == threshold is still current). Missing, unparsable and
 * future timestamps are not current.
 */
export function isMeasurementWithinThreshold(
  timestamp: unknown,
  thresholdMinutes: number,
  nowMs = Date.now(),
): boolean {
  if (timestamp === null || timestamp === undefined) return false;
  const timestampMs = new Date(timestamp as string | number | Date).getTime();
  if (!Number.isFinite(timestampMs)) return false;
  const ageMs = nowMs - timestampMs;
  return ageMs >= 0 && ageMs <= thresholdMinutes * 60 * 1000;
}

interface ClassifyInput {
  sourceId: unknown;
  hasValue: boolean;
  latestMeasurement: unknown;
}

export function classifyWaitTime(
  input: ClassifyInput,
  nowMs = Date.now(),
): WaitTimeStatus {
  if (!input.hasValue) return "none";
  if (isMonthlySource(input.sourceId)) return "monthly";
  const threshold = getLiveEstimateStaleThresholdMinutes(input.sourceId);
  return isMeasurementWithinThreshold(input.latestMeasurement, threshold, nowMs)
    ? "current"
    : "stale";
}
