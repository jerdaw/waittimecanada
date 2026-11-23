/**
 * Shared wording about the terms that apply to exported and displayed values.
 *
 * Wait Time Canada does not own the wait-time values it collects, so it cannot
 * license them. Keep every user-facing statement about data terms consistent
 * by importing from here.
 */

export const DATA_TERMS_NOTICE =
  "The Wait Time Canada software is MIT-licensed. The exported values come from third-party sources and remain subject to each source's own terms. Wait Time Canada does not grant a licence to them. Check each source's terms before reusing or redistributing the data.";

export const DATA_TERMS_HEADER_VALUE =
  "Source terms apply; no licence to source data is granted by Wait Time Canada";

export const SOFTWARE_LICENSE = "MIT";

/**
 * Display-name overrides keyed by source id. The stored source name is not
 * changed; this only corrects what users see.
 */
const SOURCE_DISPLAY_NAMES: Record<string, string> = {
  "ontario-health": "Ontario Health",
};

export function getSourceDisplayName(
  sourceId: string | null | undefined,
  storedName: string | null | undefined,
): string {
  if (sourceId && SOURCE_DISPLAY_NAMES[sourceId]) {
    return SOURCE_DISPLAY_NAMES[sourceId];
  }
  return storedName ?? sourceId ?? "";
}

export type ExportSourceRow = {
  source_id?: unknown;
  source_name?: unknown;
  source_url?: unknown;
  methodology_url?: unknown;
};

/** One attribution entry per distinct source present in the exported rows. */
export function buildSourceAttributions(rows: ExportSourceRow[]) {
  const seen = new Map<
    string,
    {
      source_id: string;
      source_name: string | null;
      source_url: string | null;
      methodology_url: string | null;
    }
  >();
  for (const row of rows) {
    if (typeof row.source_id !== "string" || seen.has(row.source_id)) continue;
    seen.set(row.source_id, {
      source_id: row.source_id,
      source_name: typeof row.source_name === "string" ? row.source_name : null,
      source_url: typeof row.source_url === "string" ? row.source_url : null,
      methodology_url:
        typeof row.methodology_url === "string" ? row.methodology_url : null,
    });
  }
  return Array.from(seen.values());
}

/** Applies display-name corrections to rows that carry a source_name. */
export function withSourceDisplayNames<T extends Record<string, unknown>>(
  rows: T[],
): T[] {
  return rows.map((row) =>
    typeof row.source_id === "string" && "source_name" in row
      ? {
          ...row,
          source_name: getSourceDisplayName(
            row.source_id,
            row.source_name as string | null,
          ),
        }
      : row,
  );
}
