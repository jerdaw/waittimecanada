interface OccupancyFreshnessInput {
  hasObservations: boolean;
  latestObservation: unknown;
  sourceStatus: unknown;
  sourceLastRun: unknown;
  consecutiveFailures: unknown;
}

function isWithinFreshnessWindow(
  value: unknown,
  staleThresholdMinutes: number,
  nowMs: number,
): boolean {
  if (value === null || value === undefined) return false;

  const timestampMs = new Date(value as string | number | Date).getTime();
  if (!Number.isFinite(timestampMs)) return false;

  const ageMs = nowMs - timestampMs;
  return ageMs >= 0 && ageMs <= staleThresholdMinutes * 60 * 1000;
}

export function isCurrentOccupancyAvailable(
  input: OccupancyFreshnessInput,
  staleThresholdMinutes: number,
  nowMs = Date.now(),
): boolean {
  return (
    input.hasObservations &&
    input.sourceStatus === "healthy" &&
    Number(input.consecutiveFailures ?? 0) === 0 &&
    isWithinFreshnessWindow(
      input.latestObservation,
      staleThresholdMinutes,
      nowMs,
    ) &&
    isWithinFreshnessWindow(input.sourceLastRun, staleThresholdMinutes, nowMs)
  );
}
