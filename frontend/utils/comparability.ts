export interface Methodology {
  metric_family: string;
  start_event: string;
  end_event: string;
  statistic_type: string;
  patient_scope: string;
}

export interface MethodologySource {
  id: string;
  name: string;
  province: string;
  default_metric_family: string;
  default_start_event: string;
  default_end_event: string;
  default_statistic_type: string;
  default_patient_scope?: string | null;
}

export type ComparabilityDimensionKey =
  | "metric_family"
  | "start_event"
  | "end_event"
  | "statistic_type"
  | "patient_scope";

export type ComparabilityLevel = "comparable" | "partial" | "not-comparable";

export interface ComparabilityDimension {
  key: ComparabilityDimensionKey;
  left_value: string;
  right_value: string;
  matches: boolean;
}

type MethodologyLike = Methodology | MethodologySource;

const COMPARABILITY_DIMENSION_KEYS: ComparabilityDimensionKey[] = [
  "metric_family",
  "start_event",
  "end_event",
  "statistic_type",
  "patient_scope",
];

export function getComparabilityDimensions(
  a: MethodologyLike,
  b: MethodologyLike,
): ComparabilityDimension[] {
  return COMPARABILITY_DIMENSION_KEYS.map((key) => {
    const leftValue = getMethodologyValue(a, key);
    const rightValue = getMethodologyValue(b, key);

    return {
      key,
      left_value: leftValue ?? "Unknown",
      right_value: rightValue ?? "Unknown",
      matches: typeof leftValue === "string" && leftValue === rightValue,
    };
  });
}

export function getComparabilityMatchCount(
  a: MethodologyLike,
  b: MethodologyLike,
) {
  return getComparabilityDimensions(a, b).filter(
    (dimension) => dimension.matches,
  ).length;
}

export function areMethodologiesComparable(a: Methodology, b: Methodology) {
  return (
    getComparabilityMatchCount(a, b) === COMPARABILITY_DIMENSION_KEYS.length
  );
}

export function getComparabilityLevel(
  a: MethodologySource,
  b: MethodologySource,
): ComparabilityLevel {
  if (a.id === b.id) return "comparable";

  const matches = getComparabilityMatchCount(a, b);
  if (matches === COMPARABILITY_DIMENSION_KEYS.length) return "comparable";
  if (matches >= 2) return "partial";
  return "not-comparable";
}

export function generateDivergenceBrief(
  a: Methodology,
  b: Methodology,
): string | null {
  if (areMethodologiesComparable(a, b)) return null;

  const differences = getComparabilityDimensions(a, b)
    .filter((dimension) => !dimension.matches)
    .map((dimension) => {
      switch (dimension.key) {
        case "metric_family":
          return `Different metrics: ${dimension.left_value} vs ${dimension.right_value}`;
        case "start_event":
          return `Different start points: ${dimension.left_value} vs ${dimension.right_value}`;
        case "end_event":
          return `Different end points: ${dimension.left_value} vs ${dimension.right_value}`;
        case "statistic_type":
          return `Different statistics: ${dimension.left_value} vs ${dimension.right_value}`;
        case "patient_scope":
          return dimension.left_value === "Unknown" ||
            dimension.right_value === "Unknown"
            ? "Patient scope is unknown for one or both measurements"
            : `Different patient scopes: ${dimension.left_value} vs ${dimension.right_value}`;
      }
    });

  return (
    "Methodology Divergence: Direct comparison is scientifically invalid. " +
    differences.join("; ") +
    "."
  );
}

export function buildUniquePairwiseComparisons<T extends MethodologySource>(
  sources: T[],
) {
  const pairs: Array<{ left: T; right: T; level: ComparabilityLevel }> = [];

  for (let index = 0; index < sources.length; index += 1) {
    for (
      let compareIndex = index + 1;
      compareIndex < sources.length;
      compareIndex += 1
    ) {
      pairs.push({
        left: sources[index],
        right: sources[compareIndex],
        level: getComparabilityLevel(sources[index], sources[compareIndex]),
      });
    }
  }

  return pairs;
}

function getMethodologyValue(
  source: MethodologyLike,
  key: ComparabilityDimensionKey,
) {
  if ("metric_family" in source) {
    return source[key];
  }

  switch (key) {
    case "metric_family":
      return source.default_metric_family;
    case "start_event":
      return source.default_start_event;
    case "end_event":
      return source.default_end_event;
    case "statistic_type":
      return source.default_statistic_type;
    case "patient_scope":
      return source.default_patient_scope ?? null;
  }
}
