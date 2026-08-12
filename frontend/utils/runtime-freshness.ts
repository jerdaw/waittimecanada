import { DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES } from "@/utils/live-scraper-sources";

export function resolveHeartbeatStaleThresholdMinutes(
  rawValue = process.env.HEARTBEAT_STALE_THRESHOLD_MINUTES,
): number {
  if (rawValue === undefined || rawValue.trim() === "") {
    return DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES;
  }

  const parsed = Number(rawValue);
  return Number.isFinite(parsed) && parsed > 0
    ? parsed
    : DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES;
}
