"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  buildUniquePairwiseComparisons,
  getComparabilityDimensions,
  getComparabilityLevel,
  getComparabilityMatchCount,
  type ComparabilityDimension,
  type ComparabilityLevel,
  type MethodologySource,
} from "@/utils/comparability";

interface ComparabilityMatrixProps {
  sources: MethodologySource[];
}

function getComparabilityColor(level: ComparabilityLevel): string {
  switch (level) {
    case "comparable":
      return "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800";
    case "partial":
      return "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800";
    case "not-comparable":
      return "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800";
  }
}

function getComparabilityIcon(level: ComparabilityLevel): string {
  switch (level) {
    case "comparable":
      return "✓";
    case "partial":
      return "⚠";
    case "not-comparable":
      return "✗";
  }
}

function exportMatrixToCSV(
  sources: MethodologySource[],
  tLevels: (key: string) => string,
) {
  // Build CSV content
  const rows: string[][] = [];

  // Header row
  const header = ["Province", ...sources.map((s) => s.province)];
  rows.push(header);

  // Data rows
  sources.forEach((rowSource) => {
    const row = [rowSource.province];
    sources.forEach((colSource) => {
      const level = getComparabilityLevel(rowSource, colSource);
      // Determine label key based on level
      let labelKey = "notComparable";
      if (level === "comparable") labelKey = "comparable";
      else if (level === "partial") labelKey = "partial";

      row.push(tLevels(labelKey));
    });
    rows.push(row);
  });

  // Convert to CSV string
  const csvContent = rows
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  // Download
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `comparability-matrix-${new Date().toISOString().split("T")[0]}.csv`,
  );
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function ComparabilityMatrix({ sources }: ComparabilityMatrixProps) {
  const t = useTranslations("Methods.ComparabilityMatrix");
  const [selectedCell, setSelectedCell] = useState<{
    row: MethodologySource;
    col: MethodologySource;
  } | null>(null);
  const searchParams = useSearchParams();
  const router = useRouter();

  // Read URL params on mount to pre-select comparison
  useEffect(() => {
    const compareParam = searchParams.get("compare");
    if (compareParam && sources.length > 0) {
      const [prov1, prov2] = compareParam.split(",");
      const source1 = sources.find((s) => s.province === prov1);
      const source2 = sources.find((s) => s.province === prov2);
      if (source1 && source2) {
        setSelectedCell({ row: source1, col: source2 });
      }
    }
  }, [searchParams, sources]);

  const handleCellClick = (
    rowSource: MethodologySource,
    colSource: MethodologySource,
  ) => {
    setSelectedCell({ row: rowSource, col: colSource });

    // Update URL with deep link
    if (rowSource.id !== colSource.id) {
      const params = new URLSearchParams(searchParams.toString());
      params.set("compare", `${rowSource.province},${colSource.province}`);
      router.replace(`?${params.toString()}`, { scroll: false });
    }
  };

  const getComparabilityLabel = (level: ComparabilityLevel): string => {
    switch (level) {
      case "comparable":
        return t("levels.comparable");
      case "partial":
        return t("levels.partial");
      case "not-comparable":
        return t("levels.notComparable");
    }
  };

  if (sources.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        {t("noData")}
      </div>
    );
  }

  const pairwiseComparisons = buildUniquePairwiseComparisons(sources);
  const selectedLevel = selectedCell
    ? getComparabilityLevel(selectedCell.row, selectedCell.col)
    : null;
  const selectedDimensions = selectedCell
    ? getComparabilityDimensions(selectedCell.row, selectedCell.col)
    : [];
  const selectedMatchCount = selectedCell
    ? getComparabilityMatchCount(selectedCell.row, selectedCell.col)
    : 0;

  return (
    <div className="space-y-6">
      {/* Matrix */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full align-middle">
          <table className="min-w-full border-collapse">
            <thead>
              <tr>
                <th className="p-3 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"></th>
                {sources.map((source) => (
                  <th
                    key={source.id}
                    className="p-3 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-semibold text-slate-700 dark:text-slate-200"
                  >
                    {source.province}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sources.map((rowSource) => (
                <tr key={rowSource.id}>
                  <th className="p-3 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-left text-sm font-semibold text-slate-700 dark:text-slate-200">
                    {rowSource.province}
                  </th>
                  {sources.map((colSource) => {
                    const level = getComparabilityLevel(rowSource, colSource);
                    const isSelected =
                      selectedCell?.row.id === rowSource.id &&
                      selectedCell?.col.id === colSource.id;

                    return (
                      <td
                        key={colSource.id}
                        className={`
                          p-3 border border-slate-200 dark:border-slate-700 text-center cursor-pointer
                          transition-all duration-200
                          ${getComparabilityColor(level)}
                          ${isSelected ? "ring-2 ring-primary ring-inset" : ""}
                          hover:opacity-80
                        `}
                        onClick={() => handleCellClick(rowSource, colSource)}
                        title={getComparabilityLabel(level)}
                      >
                        <span className="text-lg font-semibold">
                          {getComparabilityIcon(level)}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend and Export */}
      <div className="flex flex-wrap items-center justify-between gap-6">
        <div className="flex flex-wrap items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800 font-semibold">
              ✓
            </div>
            <span className="text-slate-700 dark:text-slate-300">
              {t("legend.comparable")}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800 font-semibold">
              ⚠
            </div>
            <span className="text-muted-foreground">{t("legend.partial")}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800 font-semibold">
              ✗
            </div>
            <span className="text-slate-700 dark:text-slate-300">
              {t("legend.notComparable")}
            </span>
          </div>
        </div>

        {/* Export Button */}
        <button
          onClick={() =>
            exportMatrixToCSV(sources, (key: string) => t(`levels.${key}`))
          }
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 text-sm font-medium"
          title="Export matrix as CSV"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          {t("export")}
        </button>
      </div>

      {/* Selected cell details */}
      {selectedCell && selectedCell.row.id !== selectedCell.col.id && (
        <div className="mt-6 p-6 rounded-xl border-2 border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/30">
          <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
            <h4 className="font-semibold text-blue-900 dark:text-blue-100">
              {t("comparing", {
                p1: selectedCell.row.province,
                p2: selectedCell.col.province,
              })}
            </h4>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${getComparabilityColor(
                selectedLevel ?? "not-comparable",
              )}`}
            >
              {getComparabilityIcon(selectedLevel ?? "not-comparable")}{" "}
              {getComparabilityLabel(selectedLevel ?? "not-comparable")}
            </span>
          </div>
          <p className="mb-4 text-sm text-blue-800 dark:text-blue-200">
            {t("detailsIntro")}
          </p>
          <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <SummaryCard
              label={t("summary.matchCount")}
              value={t("summary.matchCountValue", {
                count: selectedMatchCount,
                total: 4,
              })}
            />
            <SummaryCard
              label={t("summary.implication")}
              value={getClinicalImplication(
                selectedLevel ?? "not-comparable",
                t,
              )}
            />
          </div>
          <div className="space-y-2 text-sm">
            <ComparisonRow
              label={t("metrics.family")}
              dimension={selectedDimensions[0]}
              t={t}
            />
            <ComparisonRow
              label={t("metrics.start")}
              dimension={selectedDimensions[1]}
              t={t}
            />
            <ComparisonRow
              label={t("metrics.end")}
              dimension={selectedDimensions[2]}
              t={t}
            />
            <ComparisonRow
              label={t("metrics.stat")}
              dimension={selectedDimensions[3]}
              t={t}
            />
          </div>
          <p className="mt-4 text-sm text-blue-800 dark:text-blue-200">
            {selectedLevel === "comparable" && (
              <>{t("explanations.comparable")}</>
            )}
            {selectedLevel === "partial" && <>{t("explanations.partial")}</>}
            {selectedLevel === "not-comparable" && (
              <>{t("explanations.notComparable")}</>
            )}
          </p>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <h4 className="text-base font-semibold text-foreground">
            {t("pairwise.title")}
          </h4>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("pairwise.description")}
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {pairwiseComparisons.map(({ left, right, level }) => (
            <div
              key={`${left.id}-${right.id}`}
              className="rounded-xl border border-border/60 bg-card p-4 shadow-sm"
            >
              <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h5 className="font-semibold text-foreground">
                    {left.province} vs {right.province}
                  </h5>
                  <p className="text-sm text-muted-foreground">
                    {t("summary.matchCountValue", {
                      count: getComparabilityMatchCount(left, right),
                      total: 4,
                    })}
                  </p>
                </div>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${getComparabilityColor(
                    level,
                  )}`}
                >
                  {getComparabilityIcon(level)} {getComparabilityLabel(level)}
                </span>
              </div>
              <div className="space-y-2">
                {getComparabilityDimensions(left, right).map((dimension) => (
                  <PairwiseVerdictRow
                    key={`${left.id}-${right.id}-${dimension.key}`}
                    dimension={dimension}
                    t={t}
                  />
                ))}
              </div>
              <p className="mt-3 text-sm text-muted-foreground">
                {getClinicalImplication(level, t)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ComparisonRow({
  label,
  dimension,
  t,
}: {
  label: string;
  dimension: ComparabilityDimension;
  t: ReturnType<typeof useTranslations>;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-blue-200 dark:border-blue-800 last:border-0">
      <span className="font-medium text-blue-900 dark:text-blue-100">
        {label}:
      </span>
      <div className="flex items-center gap-2 flex-wrap justify-end">
        <code
          className={`px-2 py-1 rounded text-xs ${dimension.matches ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300" : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"}`}
        >
          {dimension.left_value}
        </code>
        <span className="text-blue-400 dark:text-blue-500">
          {dimension.matches ? "=" : "≠"}
        </span>
        <code
          className={`px-2 py-1 rounded text-xs ${dimension.matches ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300" : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"}`}
        >
          {dimension.right_value}
        </code>
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
            dimension.matches
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
              : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
          }`}
        >
          {dimension.matches ? t("verdicts.match") : t("verdicts.mismatch")}
        </span>
      </div>
    </div>
  );
}

function PairwiseVerdictRow({
  dimension,
  t,
}: {
  dimension: ComparabilityDimension;
  t: ReturnType<typeof useTranslations>;
}) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-border/50 bg-muted/30 px-3 py-2 text-sm">
      <div>
        <div className="font-medium text-foreground">
          {t(`metrics.${dimensionToMetricKey(dimension.key)}`)}
        </div>
        <div className="mt-1 text-xs text-muted-foreground">
          {dimension.left_value} vs {dimension.right_value}
        </div>
      </div>
      <span
        className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
          dimension.matches
            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
            : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
        }`}
      >
        {dimension.matches ? t("verdicts.match") : t("verdicts.mismatch")}
      </span>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-blue-200 dark:border-blue-800 bg-white/60 dark:bg-slate-900/40 p-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-300">
        {label}
      </div>
      <div className="mt-1 text-sm text-blue-900 dark:text-blue-100">
        {value}
      </div>
    </div>
  );
}

function dimensionToMetricKey(key: ComparabilityDimension["key"]) {
  switch (key) {
    case "metric_family":
      return "family";
    case "start_event":
      return "start";
    case "end_event":
      return "end";
    case "statistic_type":
      return "stat";
  }
}

function getClinicalImplication(
  level: ComparabilityLevel,
  t: ReturnType<typeof useTranslations>,
) {
  switch (level) {
    case "comparable":
      return t("implications.comparable");
    case "partial":
      return t("implications.partial");
    case "not-comparable":
      return t("implications.notComparable");
  }
}
