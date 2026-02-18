export type IncomeQuintile = 0 | 1 | 2 | 3 | 4 | 5;

export interface EquityFeatureProperties {
  tract_id: string;
  tract_name: string;
  income_quintile: IncomeQuintile;
  median_household_income: number | null;
  population_2021?: number | null;
  short_income_suppressed?: boolean | null;
  long_income_suppressed?: boolean | null;
  is_placeholder: boolean;
}

export interface EquityPolygonGeometry {
  type: "Polygon";
  coordinates: number[][][];
}

export interface EquityMultiPolygonGeometry {
  type: "MultiPolygon";
  coordinates: number[][][][];
}

export type EquityGeometry = EquityPolygonGeometry | EquityMultiPolygonGeometry;

export interface EquityFeature {
  type: "Feature";
  id: string;
  geometry: EquityGeometry;
  properties: EquityFeatureProperties;
}

export interface EquityFeatureCollection {
  type: "FeatureCollection";
  features: EquityFeature[];
}

export interface EquityLayerMetadata {
  province: string;
  source: string;
  attribution: string;
  generated_at: string;
  is_placeholder: boolean;
  note?: string;
  source_file?: string;
  optimized_geometry?: boolean;
  reference_year?: number | null;
  interpretation?: string;
  causal_inference?: boolean;
  temporal_alignment_note?: string;
}

export interface EquityLayerSuccessResponse {
  success: true;
  data: EquityFeatureCollection;
  metadata: EquityLayerMetadata;
}

export interface EquityLayerErrorResponse {
  success: false;
  error: string;
  setup_required?: boolean;
  setup_steps?: string[];
}

export type EquityLayerApiResponse =
  | EquityLayerSuccessResponse
  | EquityLayerErrorResponse;

export const EQUITY_QUINTILE_COLORS: Record<IncomeQuintile, string> = {
  0: "#CBD5E1",
  1: "#fee5d9",
  2: "#fcae91",
  3: "#fb6a4a",
  4: "#de2d26",
  5: "#a50f15",
};
