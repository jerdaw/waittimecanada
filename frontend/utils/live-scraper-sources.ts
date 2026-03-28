export const ACTIVE_LIVE_SCRAPER_SOURCE_IDS = [
  "quebec-msss",
  "ontario-health",
  "alberta-ahs",
  "bc-phsa",
] as const;

export const LIVE_SCRAPER_CADENCE_LABEL = "hourly";
export const EXPECTED_SCRAPER_RUNS_PER_DAY = 24;
export const EXPECTED_SCRAPER_INTERVAL_MINUTES = 60;

const ACTIVE_LIVE_SCRAPER_SOURCE_ID_SET = new Set<string>(
  ACTIVE_LIVE_SCRAPER_SOURCE_IDS,
);

export function isActiveLiveScraperSource(sourceId: string): boolean {
  return ACTIVE_LIVE_SCRAPER_SOURCE_ID_SET.has(sourceId);
}

export function getExpectedRunsForDays(days: number): number {
  return EXPECTED_SCRAPER_RUNS_PER_DAY * days;
}
