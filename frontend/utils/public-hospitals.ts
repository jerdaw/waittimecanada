import type { Hospital } from "@/app/api/hospitals/route";
import type { PublicCoverage } from "@/types/coverage";
import { getDb } from "@/utils/db";
import { buildServerCacheKey, getOrSetServerCache } from "@/utils/server-cache";

const HOSPITALS_CACHE_TTL_MS = 300_000;

interface PublicHospitalQuery {
  province?: string;
  page?: number;
  limit?: number;
  hasPagination?: boolean;
}

export interface PublicHospitalPayload {
  success: true;
  count: number;
  data: Hospital[];
  coverage: PublicCoverage;
}

function toIsoString(value: unknown): string | undefined {
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "string") return new Date(value).toISOString();
  return undefined;
}

async function queryPublicHospitals({
  province,
  page = 1,
  limit = 20,
  hasPagination = false,
}: PublicHospitalQuery): Promise<PublicHospitalPayload> {
  const sql = getDb();

  let query = `
    SELECT
      h.id,
      h.name,
      h.province,
      h.city,
      h.latitude,
      h.longitude,
      h.is_verified,
      h.is_visible,
      h.source_id,
      s.telehealth_name,
      s.telehealth_number,
      m.value as current_wait_time,
      m.timestamp_utc as last_updated,
      m.metric_family,
      m.start_event,
      m.end_event,
      m.statistic_type,
      m.patient_scope,
      occ.value as occupancy_percentage,
      occ.timestamp_utc as occupancy_updated
    FROM hospitals h
    LEFT JOIN sources s ON s.id = h.source_id
    LEFT JOIN LATERAL (
      SELECT
        value,
        timestamp_utc,
        metric_family,
        start_event,
        end_event,
        statistic_type,
        patient_scope
      FROM measurements
      WHERE hospital_id = h.id
        AND metric_family = 'TIME_TO_PROVIDER'
      ORDER BY timestamp_utc DESC
      LIMIT 1
    ) m ON true
    LEFT JOIN LATERAL (
      SELECT
        value,
        timestamp_utc
      FROM measurements
      WHERE hospital_id = h.id
        AND metric_family = 'STRETCHER_OCCUPANCY'
      ORDER BY timestamp_utc DESC
      LIMIT 1
    ) occ ON true
    WHERE h.is_visible = true AND h.is_verified = true
  `;

  const params: Array<string | number> = [];
  if (province) {
    params.push(province);
    query += ` AND h.province = $${params.length}`;
  }

  query += " ORDER BY h.name";

  if (hasPagination) {
    params.push(limit);
    const limitPlaceholder = `$${params.length}`;
    params.push((page - 1) * limit);
    const offsetPlaceholder = `$${params.length}`;
    query += ` LIMIT ${limitPlaceholder} OFFSET ${offsetPlaceholder}`;
  }

  const hospitalRows = await sql.unsafe(query, params);
  const coverageRows = await sql`
    SELECT
      COUNT(*)::int AS hospital_count,
      COUNT(DISTINCT h.province)::int AS province_count,
      (
        SELECT MAX(m.timestamp_utc)
        FROM measurements m
        JOIN hospitals measured_hospital ON measured_hospital.id = m.hospital_id
        WHERE measured_hospital.is_visible = true
          AND measured_hospital.is_verified = true
      ) AS latest_measurement_at
    FROM hospitals h
    WHERE h.is_visible = true
      AND h.is_verified = true
  `;

  const coverageRow = coverageRows[0];
  const hospitals: Hospital[] = hospitalRows.map((row) => ({
    id: String(row.id),
    name: String(row.name),
    province: String(row.province),
    city: String(row.city),
    latitude: Number(row.latitude),
    longitude: Number(row.longitude),
    is_verified: Boolean(row.is_verified),
    is_visible: Boolean(row.is_visible),
    source_id: String(row.source_id),
    current_wait_time:
      row.current_wait_time == null ? undefined : Number(row.current_wait_time),
    last_updated: toIsoString(row.last_updated),
    metric_family:
      row.metric_family == null ? undefined : String(row.metric_family),
    start_event: row.start_event == null ? undefined : String(row.start_event),
    end_event: row.end_event == null ? undefined : String(row.end_event),
    statistic_type:
      row.statistic_type == null ? undefined : String(row.statistic_type),
    patient_scope:
      row.patient_scope == null ? undefined : String(row.patient_scope),
    telehealth_name:
      row.telehealth_name == null ? undefined : String(row.telehealth_name),
    telehealth_number:
      row.telehealth_number == null ? undefined : String(row.telehealth_number),
    occupancy_percentage:
      row.occupancy_percentage == null
        ? undefined
        : Number(row.occupancy_percentage),
    occupancy_updated: toIsoString(row.occupancy_updated),
  }));

  return {
    success: true,
    count: hospitals.length,
    data: hospitals,
    coverage: {
      hospital_count: Number(coverageRow?.hospital_count ?? 0),
      province_count: Number(coverageRow?.province_count ?? 0),
      generated_at: new Date().toISOString(),
      latest_measurement_at:
        toIsoString(coverageRow?.latest_measurement_at) ?? null,
    },
  };
}

export function getPublicHospitals(
  options: PublicHospitalQuery = {},
): Promise<PublicHospitalPayload> {
  const { province, page = 1, limit = 20, hasPagination = false } = options;

  return getOrSetServerCache(
    buildServerCacheKey("api:hospitals", {
      province: province ?? "all",
      page: hasPagination ? page : undefined,
      limit: hasPagination ? limit : undefined,
    }),
    HOSPITALS_CACHE_TTL_MS,
    () => queryPublicHospitals(options),
  );
}
