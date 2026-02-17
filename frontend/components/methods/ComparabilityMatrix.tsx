"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

interface Source {
  id: string;
  name: string;
  province: string;
  default_metric_family: string;
  default_start_event: string;
  default_end_event: string;
  default_statistic_type: string;
}

interface ComparabilityMatrixProps {
  sources: Source[];
}

type ComparabilityLevel = "comparable" | "partial" | "not-comparable";

function areComparable(a: Source, b: Source): ComparabilityLevel {
  // Same source is always comparable
  if (a.id === b.id) return "comparable";

  // Check all four dimensions
  const metricMatch = a.default_metric_family === b.default_metric_family;
  const startMatch = a.default_start_event === b.default_start_event;
  const endMatch = a.default_end_event === b.default_end_event;
  const statMatch = a.default_statistic_type === b.default_statistic_type;

  const matches = [metricMatch, startMatch, endMatch, statMatch].filter(
    Boolean,
  ).length;

  if (matches === 4) return "comparable";
  if (matches >= 2) return "partial";
  return "not-comparable";
}

function getComparabilityColor(level: ComparabilityLevel): string {
  switch (level) {
    case "comparable":
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    case "partial":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "not-comparable":
      return "bg-red-100 text-red-700 border-red-200";
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

function exportMatrixToCSV(sources: Source[], tLevels: any) {
  // Build CSV content
  const rows: string[][] = [];

  // Header row
  const header = ["Province", ...sources.map((s) => s.province)];
  rows.push(header);

  // Data rows
  sources.forEach((rowSource) => {
    const row = [rowSource.province];
    sources.forEach((colSource) => {
      const level = areComparable(rowSource, colSource);
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
  const t = useTranslations('Methods.ComparabilityMatrix');
  const [selectedCell, setSelectedCell] = useState<{
    row: Source;
    col: Source;
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

  const handleCellClick = (rowSource: Source, colSource: Source) => {
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
        return t('levels.comparable');
      case "partial":
        return t('levels.partial');
      case "not-comparable":
        return t('levels.notComparable');
    }
  };

  if (sources.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        {t('noData')}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Matrix */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full align-middle">
          <table className="min-w-full border-collapse">
            <thead>
              <tr>
                <th className="p-3 border border-slate-200 bg-slate-50"></th>
                {sources.map((source) => (
                  <th
                    key={source.id}
                    className="p-3 border border-slate-200 bg-slate-50 text-sm font-semibold text-slate-700"
                  >
                    {source.province}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sources.map((rowSource) => (
                <tr key={rowSource.id}>
                  <th className="p-3 border border-slate-200 bg-slate-50 text-left text-sm font-semibold text-slate-700">
                    {rowSource.province}
                  </th>
                  {sources.map((colSource) => {
                    const level = areComparable(rowSource, colSource);
                    const isSelected =
                      selectedCell?.row.id === rowSource.id &&
                      selectedCell?.col.id === colSource.id;

                    return (
                      <td
                        key={colSource.id}
                        className={`
                          p-3 border border-slate-200 text-center cursor-pointer
                          transition-all duration-200
                          ${getComparabilityColor(level)}
                          ${isSelected ? "ring-2 ring-blue-500 ring-inset" : ""}
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
            <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-emerald-100 text-emerald-700 border-emerald-200 font-semibold">
              ✓
            </div>
            <span className="text-slate-700">{t('legend.comparable')}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-amber-100 text-amber-700 border-amber-200 font-semibold">
              ⚠
            </div>
            <span className="text-slate-700">
              {t('legend.partial')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-red-100 text-red-700 border-red-200 font-semibold">
              ✗
            </div>
            <span className="text-slate-700">{t('legend.notComparable')}</span>
          </div>
        </div>

        {/* Export Button */}
        <button
          onClick={() => exportMatrixToCSV(sources, (key: string) => t(`levels.${key}`))}
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
          {t('export')}
        </button>
      </div>

      {/* Selected cell details */}
      {selectedCell && selectedCell.row.id !== selectedCell.col.id && (
        <div className="mt-6 p-6 rounded-xl border-2 border-blue-200 bg-blue-50">
          <h4 className="font-semibold text-blue-900 mb-3">
            {t('comparing', {p1: selectedCell.row.province, p2: selectedCell.col.province})}
          </h4>
          <div className="space-y-2 text-sm">
            <ComparisonRow
              label={t('metrics.family')}
              value1={selectedCell.row.default_metric_family}
              value2={selectedCell.col.default_metric_family}
            />
            <ComparisonRow
              label={t('metrics.start')}
              value1={selectedCell.row.default_start_event}
              value2={selectedCell.col.default_start_event}
            />
            <ComparisonRow
              label={t('metrics.end')}
              value1={selectedCell.row.default_end_event}
              value2={selectedCell.col.default_end_event}
            />
            <ComparisonRow
              label={t('metrics.stat')}
              value1={selectedCell.row.default_statistic_type}
              value2={selectedCell.col.default_statistic_type}
            />
          </div>
          <p className="mt-4 text-sm text-blue-800">
            {areComparable(selectedCell.row, selectedCell.col) ===
              "comparable" && (
              <>
                {t('explanations.comparable')}
              </>
            )}
            {areComparable(selectedCell.row, selectedCell.col) ===
              "partial" && (
              <>
                {t('explanations.partial')}
              </>
            )}
            {areComparable(selectedCell.row, selectedCell.col) ===
              "not-comparable" && (
              <>
                {t('explanations.notComparable')}
              </>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

function ComparisonRow({
  label,
  value1,
  value2,
}: {
  label: string;
  value1: string;
  value2: string;
}) {
  const matches = value1 === value2;

  return (
    <div className="flex items-center justify-between py-2 border-b border-blue-200 last:border-0">
      <span className="font-medium text-blue-900">{label}:</span>
      <div className="flex items-center gap-2">
        <code
          className={`px-2 py-1 rounded text-xs ${matches ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}
        >
          {value1}
        </code>
        <span className="text-blue-400">{matches ? "=" : "≠"}</span>
        <code
          className={`px-2 py-1 rounded text-xs ${matches ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}
        >
          {value2}
        </code>
      </div>
    </div>
  );
}
