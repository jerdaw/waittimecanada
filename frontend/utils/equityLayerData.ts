import { promises as fs } from "fs";
import path from "path";
import type {
  EquityFeature,
  EquityFeatureCollection,
  IncomeQuintile,
} from "@/utils/equity";

const PROVINCE_TO_FILES: Record<
  string,
  { canonical: string; optimized?: string }
> = {
  ON: {
    canonical: "ontario-equity-layer.geojson",
    optimized: "ontario-equity-layer.optimized.geojson",
  },
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : null;
}

function parseNumberOrNull(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.trim().replace(/,/g, "");
    if (!normalized) return null;
    const parsed = Number(normalized);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return null;
}

function parseBooleanOrNull(value: unknown): boolean | null {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (normalized === "true") return true;
    if (normalized === "false") return false;
  }
  return null;
}

function normalizeQuintile(value: unknown): IncomeQuintile {
  const parsed = parseNumberOrNull(value);
  if (parsed === null) return 0;
  const rounded = Math.round(parsed);
  if (rounded <= 0) return 0;
  if (rounded >= 5) return 5;
  return rounded as IncomeQuintile;
}

function normalizeGeometry(value: unknown): EquityFeature["geometry"] | null {
  const geometry = asRecord(value);
  if (!geometry) return null;
  const type = geometry.type;
  if (type !== "Polygon" && type !== "MultiPolygon") {
    return null;
  }
  const coordinates = geometry.coordinates;
  if (!Array.isArray(coordinates)) {
    return null;
  }
  if (type === "Polygon") {
    return {
      type: "Polygon",
      coordinates: coordinates as number[][][],
    };
  }
  return {
    type: "MultiPolygon",
    coordinates: coordinates as number[][][][],
  };
}

function normalizeFeature(rawFeature: unknown): EquityFeature | null {
  const feature = asRecord(rawFeature);
  if (!feature) return null;
  const properties = asRecord(feature.properties) ?? {};
  const tractId =
    String(
      properties.tract_id ??
        properties.CTUID ??
        properties.ctuid ??
        feature.id ??
        "",
    ).trim() || null;
  if (!tractId) return null;

  const tractName =
    String(
      properties.tract_name ??
        properties.CTNAME ??
        properties.ctname ??
        tractId,
    ).trim() || tractId;

  const geometry = normalizeGeometry(feature.geometry);
  if (!geometry) return null;
  const rawPlaceholderFlag = properties.is_placeholder;
  const isPlaceholder =
    typeof rawPlaceholderFlag === "boolean" ? rawPlaceholderFlag : true;

  return {
    type: "Feature",
    id: tractId,
    geometry,
    properties: {
      tract_id: tractId,
      tract_name: tractName,
      income_quintile: normalizeQuintile(properties.income_quintile),
      median_household_income: parseNumberOrNull(
        properties.median_household_income,
      ),
      population_2021: parseNumberOrNull(
        properties.population_2021 ?? properties.pop_2021,
      ),
      short_income_suppressed: parseBooleanOrNull(
        properties.short_income_suppressed,
      ),
      long_income_suppressed: parseBooleanOrNull(
        properties.long_income_suppressed,
      ),
      is_placeholder: isPlaceholder,
    },
  };
}

async function resolveLayerPath(fileName: string): Promise<string> {
  const candidates = [
    path.join(process.cwd(), "backend", "data", "layers", fileName),
    path.join(process.cwd(), "..", "backend", "data", "layers", fileName),
  ];

  for (const candidate of candidates) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {
      // Continue scanning candidates.
    }
  }

  throw new Error(`Equity layer file not found for ${fileName}`);
}

async function resolveLayerPathFromCandidates(
  fileNames: string[],
): Promise<{ fileName: string; layerPath: string }> {
  for (const fileName of fileNames) {
    try {
      const layerPath = await resolveLayerPath(fileName);
      return { fileName, layerPath };
    } catch {
      // Try next candidate.
    }
  }
  throw new Error(
    `Equity layer file not found for candidates: ${fileNames.join(", ")}`,
  );
}

export function isSupportedEquityProvince(province: string): boolean {
  return province in PROVINCE_TO_FILES;
}

export async function loadEquityLayerForProvinceWithSource(
  province: string,
): Promise<{ data: EquityFeatureCollection; source_file: string }> {
  const files = PROVINCE_TO_FILES[province];
  if (!files) {
    throw new Error(`Unsupported province for equity layer: ${province}`);
  }
  const candidateFiles = [files.optimized, files.canonical].filter(
    (value): value is string => Boolean(value),
  );
  const { fileName, layerPath } =
    await resolveLayerPathFromCandidates(candidateFiles);

  const fileContents = await fs.readFile(layerPath, "utf-8");
  const payload = JSON.parse(fileContents) as Record<string, unknown>;
  const rawFeatures = Array.isArray(payload.features) ? payload.features : [];
  const features = rawFeatures
    .map(normalizeFeature)
    .filter((item): item is EquityFeature => item !== null);

  return {
    data: {
      type: "FeatureCollection",
      features,
    },
    source_file: fileName,
  };
}

export async function loadEquityLayerForProvince(
  province: string,
): Promise<EquityFeatureCollection> {
  const { data } = await loadEquityLayerForProvinceWithSource(province);
  return data;
}
