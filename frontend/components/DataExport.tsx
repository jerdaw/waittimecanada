"use client";

import { useState } from "react";
import { Download, FileSpreadsheet, Code, Info } from "lucide-react";

type DateRange = "24h" | "7d" | "30d" | "90d" | "6m" | "1y" | "all";
type Granularity = "raw" | "hourly" | "daily" | "weekly" | "monthly";

const DATE_RANGE_DAYS: Record<DateRange, number | null> = {
  "24h": 1,
  "7d": 7,
  "30d": 30,
  "90d": 90,
  "6m": 180,
  "1y": 365,
  all: null,
};

const GRANULARITY_LABELS: Record<Granularity, string> = {
  raw: "Raw Measurements",
  hourly: "Hourly Averages",
  daily: "Daily Averages",
  weekly: "Weekly Averages",
  monthly: "Monthly Averages",
};

export function DataExport() {
  const [province, setProvince] = useState<string>("");
  const [dateRange, setDateRange] = useState<DateRange>("7d");
  const [granularity, setGranularity] = useState<Granularity>("raw");
  const [format, setFormat] = useState<"csv" | "json">("csv");
  const [loading, setLoading] = useState(false);

  const isAggregated = granularity !== "raw";
  const rangeDays = DATE_RANGE_DAYS[dateRange];
  const rangeExceedsRaw = rangeDays !== null && rangeDays > 30;

  const handleExport = async () => {
    setLoading(true);

    const params = new URLSearchParams();
    if (province) params.set("province", province);
    params.set("format", format);
    params.set("granularity", granularity);

    // Calculate date range
    const now = new Date();
    if (dateRange !== "all") {
      const days = DATE_RANGE_DAYS[dateRange]!;
      const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      params.set("start_date", start.toISOString());
    }

    // Trigger download
    window.location.href = `/api/export?${params.toString()}`;

    // Reset loading state after a short delay (download is triggered but doesn't block)
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileSpreadsheet className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          Download Data
        </h3>
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
        Export wait time data with full methodology tags for research use. All
        exports include metric ontology columns for proper attribution.
      </p>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label
            htmlFor="province-select"
            className="block text-sm font-medium text-foreground mb-1"
          >
            Province
          </label>
          <select
            id="province-select"
            value={province}
            onChange={(e) => setProvince(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          >
            <option value="">All Provinces</option>
            <option value="ON">Ontario</option>
            <option value="QC">Quebec</option>
            <option value="AB">Alberta</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="daterange-select"
            className="block text-sm font-medium text-foreground mb-1"
          >
            Date Range
          </label>
          <select
            id="daterange-select"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as DateRange)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="6m">Last 6 Months</option>
            <option value="1y">Last Year</option>
            <option value="all">All Data</option>
          </select>
        </div>
      </div>

      {/* Granularity Selector */}
      <div className="mb-4">
        <label
          htmlFor="granularity-select"
          className="block text-sm font-medium text-foreground mb-1"
        >
          Data Granularity
        </label>
        <select
          id="granularity-select"
          value={granularity}
          onChange={(e) => setGranularity(e.target.value as Granularity)}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
        >
          {Object.entries(GRANULARITY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-muted-foreground">
          {isAggregated
            ? "Aggregated data includes mean, median, P90, min, max, and sample count per period."
            : "Raw data is available for the last 30 days. For longer ranges, use aggregated data."}
        </p>
      </div>

      {/* Warning for raw data with long range */}
      {!isAggregated && rangeExceedsRaw && (
        <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <p className="text-xs text-amber-700 dark:text-amber-400">
            Raw measurements are retained for 30 days. For ranges beyond 30
            days, switch to an aggregated granularity (daily, weekly, or
            monthly) to access permanent statistical summaries.
          </p>
        </div>
      )}

      {/* Format Toggle */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm font-medium text-foreground">Format:</span>
        <div className="flex gap-2">
          <button
            onClick={() => setFormat("csv")}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              format === "csv"
                ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600"
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            CSV
          </button>
          <button
            onClick={() => setFormat("json")}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              format === "json"
                ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600"
            }`}
          >
            <Code className="w-4 h-4" />
            JSON
          </button>
        </div>
      </div>

      {/* Download Button */}
      <button
        onClick={handleExport}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Download className="w-5 h-5" />
        {loading ? "Preparing..." : "Download Data"}
      </button>

      {/* Citation Info */}
      <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
          <div className="text-xs text-muted-foreground">
            <p className="font-medium mb-1">Suggested Citation:</p>
            <p className="italic">
              Wait Time Canada. (2026). Canadian ER Wait Time Data [Data set].
              https://wait-time.ca
            </p>
            <p className="mt-2">License: CC-BY-4.0 (Attribution Required)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
