"use client";

import { useState } from "react";

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

  const matches = [metricMatch, startMatch, endMatch, statMatch].filter(Boolean).length;

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

function getComparabilityLabel(level: ComparabilityLevel): string {
  switch (level) {
    case "comparable":
      return "Directly comparable";
    case "partial":
      return "Partially comparable";
    case "not-comparable":
      return "Not comparable";
  }
}

export function ComparabilityMatrix({ sources }: ComparabilityMatrixProps) {
  const [selectedCell, setSelectedCell] = useState<{
    row: Source;
    col: Source;
  } | null>(null);

  if (sources.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        No data sources configured yet.
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
                        onClick={() =>
                          setSelectedCell({ row: rowSource, col: colSource })
                        }
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

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-emerald-100 text-emerald-700 border-emerald-200 font-semibold">
            ✓
          </div>
          <span className="text-slate-700">Directly comparable</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-amber-100 text-amber-700 border-amber-200 font-semibold">
            ⚠
          </div>
          <span className="text-slate-700">Partially comparable (2-3 matches)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 flex items-center justify-center rounded border-2 bg-red-100 text-red-700 border-red-200 font-semibold">
            ✗
          </div>
          <span className="text-slate-700">Not comparable (0-1 matches)</span>
        </div>
      </div>

      {/* Selected cell details */}
      {selectedCell && selectedCell.row.id !== selectedCell.col.id && (
        <div className="mt-6 p-6 rounded-xl border-2 border-blue-200 bg-blue-50">
          <h4 className="font-semibold text-blue-900 mb-3">
            Comparing {selectedCell.row.province} with {selectedCell.col.province}
          </h4>
          <div className="space-y-2 text-sm">
            <ComparisonRow
              label="Metric Family"
              value1={selectedCell.row.default_metric_family}
              value2={selectedCell.col.default_metric_family}
            />
            <ComparisonRow
              label="Start Event"
              value1={selectedCell.row.default_start_event}
              value2={selectedCell.col.default_start_event}
            />
            <ComparisonRow
              label="End Event"
              value1={selectedCell.row.default_end_event}
              value2={selectedCell.col.default_end_event}
            />
            <ComparisonRow
              label="Statistic Type"
              value1={selectedCell.row.default_statistic_type}
              value2={selectedCell.col.default_statistic_type}
            />
          </div>
          <p className="mt-4 text-sm text-blue-800">
            {areComparable(selectedCell.row, selectedCell.col) === "comparable" && (
              <>
                ✓ These provinces use identical methodologies and can be directly compared.
              </>
            )}
            {areComparable(selectedCell.row, selectedCell.col) === "partial" && (
              <>
                ⚠ These provinces differ in some dimensions. Comparisons should note these
                differences.
              </>
            )}
            {areComparable(selectedCell.row, selectedCell.col) ===
              "not-comparable" && (
              <>
                ✗ These provinces use fundamentally different methodologies. Direct
                comparison is statistically invalid.
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
        <span className="text-blue-400">
          {matches ? "=" : "≠"}
        </span>
        <code
          className={`px-2 py-1 rounded text-xs ${matches ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}
        >
          {value2}
        </code>
      </div>
    </div>
  );
}
