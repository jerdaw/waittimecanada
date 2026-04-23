export type SourceDomain =
  | "provider_facility"
  | "aed"
  | "safety_alert"
  | "health_product_reference"
  | "environmental_overlay"
  | "system_context";

export type ResourceKind = "facility" | "aed";
export type FreshnessState = "show" | "warn" | "suppress";

export interface SourceStatusRecord {
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | null;
  freshness_state: FreshnessState;
}

export interface SourceCatalogRecord {
  source_id: string;
  domain: SourceDomain;
  source_name: string;
  connector_type: string;
  access_route: string;
  license_reuse_status: string;
  attribution_requirement: string;
  update_cadence: string;
  recommended_usage_mode: string;
  public_methodology_note: string | null;
  provenance_url: string;
  last_verified_at: string | null;
  last_refreshed_at: string | null;
  freshness_state: FreshnessState;
}

export interface ResourceRecord {
  id: string;
  kind: ResourceKind;
  name: string;
  province: string;
  city: string | null;
  latitude: number;
  longitude: number;
  distance_km?: number;
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | null;
  freshness_state: FreshnessState;
  caveat_class: "reference_directory" | "crowdsourced_incomplete";
  address?: string | null;
  postal_code?: string | null;
  phone?: string | null;
  website_url?: string | null;
  reference_status?: "directory_only";
  location_description?: string | null;
  access_notes?: string | null;
  crowdsourced?: true;
  completeness_status?: "incomplete";
}

export interface AlertRecord {
  id: string;
  title: string;
  summary: string;
  alert_type: string;
  published_at: string;
  updated_at?: string | null;
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | null;
  freshness_state: FreshnessState;
  caveat_class: "official_alert_feed";
  affected_products?: Array<{
    brand_name: string;
    din?: string | null;
  }>;
}

export interface AQHIRecord {
  location_name: string;
  aqhi_value: number;
  category: "low" | "moderate" | "high" | "very_high";
  issued_at: string;
  valid_until?: string | null;
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | null;
  freshness_state: FreshnessState;
  caveat_class: "official_forecast";
}

export interface SystemContextSeverityRecord {
  patient_severity: string | null;
  response_time_plan_minutes: number | null;
  planned_response_pct: number | null;
  performance_pct: number | null;
}

export interface SystemContextDispatchCentreRecord {
  id: string;
  geography_name: string;
  reporting_year: number;
  average_response_time_minutes: number | null;
  call_volume: number | null;
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | null;
  freshness_state: FreshnessState;
  caveat_class: "official_system_context";
}

export interface SystemContextParamedicServiceRecord {
  id: string;
  geography_name: string;
  reporting_year: number;
  severity_breakdown: SystemContextSeverityRecord[];
  source_id: string;
  source_name: string;
  provenance_url: string;
  last_refreshed_at: string | null;
  freshness_state: FreshnessState;
  caveat_class: "official_system_context";
}

type FreshnessThresholds = {
  showMs: number;
  warnMs: number;
};

type SourceStatusRow = {
  source_id: string;
  source_name: string;
  provenance_url: string;
  domain: SourceDomain;
  last_refreshed_at: string | Date | null;
};

type SourceCatalogRow = SourceStatusRow & {
  connector_type: string;
  access_route: string;
  license_reuse_status: string;
  attribution_requirement: string;
  update_cadence: string;
  recommended_usage_mode: string;
  public_methodology_note: string | null;
  last_verified_at: string | Date | null;
};

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

const FRESHNESS_THRESHOLDS: Record<SourceDomain, FreshnessThresholds> = {
  provider_facility: {
    showMs: 548 * DAY_MS,
    warnMs: 913 * DAY_MS,
  },
  aed: {
    showMs: 30 * DAY_MS,
    warnMs: 90 * DAY_MS,
  },
  safety_alert: {
    showMs: 24 * HOUR_MS,
    warnMs: 48 * HOUR_MS,
  },
  health_product_reference: {
    showMs: 24 * HOUR_MS,
    warnMs: 48 * HOUR_MS,
  },
  environmental_overlay: {
    showMs: 6 * HOUR_MS,
    warnMs: 12 * HOUR_MS,
  },
  system_context: {
    showMs: 30 * DAY_MS,
    warnMs: 90 * DAY_MS,
  },
};

export function toIsoTimestamp(
  value: string | Date | null | undefined,
): string | null {
  if (!value) {
    return null;
  }

  return value instanceof Date
    ? value.toISOString()
    : new Date(value).toISOString();
}

export function deriveFreshnessState(
  domain: SourceDomain,
  lastRefreshedAt: string | Date | null | undefined,
  provenanceUrl: string | null | undefined,
): FreshnessState {
  if (!provenanceUrl) {
    return "suppress";
  }

  const timestamp = toIsoTimestamp(lastRefreshedAt);
  if (!timestamp) {
    return "suppress";
  }

  const ageMs = Date.now() - new Date(timestamp).getTime();
  const thresholds = FRESHNESS_THRESHOLDS[domain];

  if (ageMs <= thresholds.showMs) {
    return "show";
  }

  if (ageMs <= thresholds.warnMs) {
    return "warn";
  }

  return "suppress";
}

export function buildSourceStatusRecords(
  rows: SourceStatusRow[],
): SourceStatusRecord[] {
  return rows.map((row) => ({
    source_id: row.source_id,
    source_name: row.source_name,
    provenance_url: row.provenance_url,
    last_refreshed_at: toIsoTimestamp(row.last_refreshed_at),
    freshness_state: deriveFreshnessState(
      row.domain,
      row.last_refreshed_at,
      row.provenance_url,
    ),
  }));
}

export function buildSourceCatalogRecords(
  rows: SourceCatalogRow[],
): SourceCatalogRecord[] {
  return rows.map((row) => ({
    source_id: row.source_id,
    domain: row.domain,
    source_name: row.source_name,
    connector_type: row.connector_type,
    access_route: row.access_route,
    license_reuse_status: row.license_reuse_status,
    attribution_requirement: row.attribution_requirement,
    update_cadence: row.update_cadence,
    recommended_usage_mode: row.recommended_usage_mode,
    public_methodology_note: row.public_methodology_note,
    provenance_url: row.provenance_url,
    last_verified_at: toIsoTimestamp(row.last_verified_at),
    last_refreshed_at: toIsoTimestamp(row.last_refreshed_at),
    freshness_state: deriveFreshnessState(
      row.domain,
      row.last_refreshed_at,
      row.provenance_url,
    ),
  }));
}

export function calculateDistanceKm(
  latitude: number,
  longitude: number,
  otherLatitude: number,
  otherLongitude: number,
): number {
  const earthRadiusKm = 6371;
  const latitudeDelta = toRadians(otherLatitude - latitude);
  const longitudeDelta = toRadians(otherLongitude - longitude);
  const a =
    Math.sin(latitudeDelta / 2) * Math.sin(latitudeDelta / 2) +
    Math.cos(toRadians(latitude)) *
      Math.cos(toRadians(otherLatitude)) *
      Math.sin(longitudeDelta / 2) *
      Math.sin(longitudeDelta / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return Number((earthRadiusKm * c).toFixed(1));
}

function toRadians(value: number) {
  return (value * Math.PI) / 180;
}
