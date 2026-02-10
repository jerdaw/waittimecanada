export type IncomeQuintile = 1 | 2 | 3 | 4 | 5;

export interface EquityFeatureProperties {
  tract_id: string;
  tract_name: string;
  income_quintile: IncomeQuintile;
  median_household_income: number;
  is_placeholder: boolean;
}

export interface EquityPolygonGeometry {
  type: "Polygon";
  coordinates: number[][][];
}

export interface EquityFeature {
  type: "Feature";
  id: string;
  geometry: EquityPolygonGeometry;
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
  note: string;
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
  1: "#fee5d9",
  2: "#fcae91",
  3: "#fb6a4a",
  4: "#de2d26",
  5: "#a50f15",
};

function rectanglePolygon(
  minLon: number,
  minLat: number,
  maxLon: number,
  maxLat: number,
): number[][][] {
  return [
    [
      [minLon, minLat],
      [maxLon, minLat],
      [maxLon, maxLat],
      [minLon, maxLat],
      [minLon, minLat],
    ],
  ];
}

const ON_PLACEHOLDER_FEATURES: EquityFeature[] = [
  {
    type: "Feature",
    id: "on-demo-1",
    geometry: {
      type: "Polygon",
      coordinates: rectanglePolygon(-79.6, 43.59, -79.42, 43.74),
    },
    properties: {
      tract_id: "on-demo-1",
      tract_name: "Toronto Core (placeholder)",
      income_quintile: 2,
      median_household_income: 67000,
      is_placeholder: true,
    },
  },
  {
    type: "Feature",
    id: "on-demo-2",
    geometry: {
      type: "Polygon",
      coordinates: rectanglePolygon(-79.42, 43.59, -79.22, 43.74),
    },
    properties: {
      tract_id: "on-demo-2",
      tract_name: "Toronto East (placeholder)",
      income_quintile: 3,
      median_household_income: 79000,
      is_placeholder: true,
    },
  },
  {
    type: "Feature",
    id: "on-demo-3",
    geometry: {
      type: "Polygon",
      coordinates: rectanglePolygon(-75.88, 45.3, -75.55, 45.47),
    },
    properties: {
      tract_id: "on-demo-3",
      tract_name: "Ottawa Metro (placeholder)",
      income_quintile: 4,
      median_household_income: 91000,
      is_placeholder: true,
    },
  },
  {
    type: "Feature",
    id: "on-demo-4",
    geometry: {
      type: "Polygon",
      coordinates: rectanglePolygon(-81.34, 42.9, -81.05, 43.12),
    },
    properties: {
      tract_id: "on-demo-4",
      tract_name: "Southwest Ontario (placeholder)",
      income_quintile: 1,
      median_household_income: 56000,
      is_placeholder: true,
    },
  },
  {
    type: "Feature",
    id: "on-demo-5",
    geometry: {
      type: "Polygon",
      coordinates: rectanglePolygon(-89.65, 48.33, -89.1, 48.53),
    },
    properties: {
      tract_id: "on-demo-5",
      tract_name: "Northwest Ontario (placeholder)",
      income_quintile: 2,
      median_household_income: 61000,
      is_placeholder: true,
    },
  },
];

export function buildPlaceholderEquityFeatureCollection(
  province: string,
): EquityFeatureCollection {
  if (province === "ON") {
    return {
      type: "FeatureCollection",
      features: ON_PLACEHOLDER_FEATURES,
    };
  }

  return {
    type: "FeatureCollection",
    features: [],
  };
}
