/**
 * Helper to determine if data is fresh (< 30 mins)
 */
export function isRecent(dateStr: string | undefined | null) {
  if (!dateStr) return false;
  const updated = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - updated.getTime();
  return diffMs < 30 * 60 * 1000; // 30 mins
}
