"use client";

import { useEffect, useRef, useState } from "react";
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

const RAW_EXPORT_PAGE_SIZE = 10000;

function getNextPagePath(linkHeader: string | null, requestUrl: string) {
  const target = linkHeader?.match(/<([^>]+)>\s*;\s*rel="?next"?/i)?.[1];
  if (!target) {
    return null;
  }

  const request = new URL(requestUrl, window.location.origin);
  const next = new URL(target, request);
  const requestFilters = new URL(request.href);
  const nextFilters = new URL(next.href);
  requestFilters.searchParams.delete("cursor");
  nextFilters.searchParams.delete("cursor");

  if (
    next.origin !== window.location.origin ||
    next.pathname !== request.pathname ||
    nextFilters.search !== requestFilters.search
  ) {
    throw new Error("The export returned an unsafe next-page link.");
  }

  return `${next.pathname}${next.search}`;
}

function downloadBlob(blob: Blob, format: "csv" | "json", pageNumber: number) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const date = new Date().toISOString().split("T")[0];
  link.href = objectUrl;
  link.download = `wait-time-ca-export-${date}-page-${String(pageNumber).padStart(3, "0")}.${format}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
}

export function DataExport() {
  const [province, setProvince] = useState<string>("");
  const [dateRange, setDateRange] = useState<DateRange>("7d");
  const [granularity, setGranularity] = useState<Granularity>("raw");
  const [format, setFormat] = useState<"csv" | "json">("csv");
  const [loading, setLoading] = useState(false);
  const [nextPageUrl, setNextPageUrl] = useState<string | null>(null);
  const [downloadedPages, setDownloadedPages] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const requestSequence = useRef(0);
  const activeRequest = useRef<AbortController | null>(null);

  const isAggregated = granularity !== "raw";
  const rangeDays = DATE_RANGE_DAYS[dateRange];
  const rangeExceedsRaw = rangeDays !== null && rangeDays > 30;

  const resetPaginationState = () => {
    requestSequence.current += 1;
    activeRequest.current?.abort();
    activeRequest.current = null;
    setLoading(false);
    setNextPageUrl(null);
    setDownloadedPages(0);
    setProgressMessage("");
    setDownloadError("");
  };

  useEffect(
    () => () => {
      requestSequence.current += 1;
      activeRequest.current?.abort();
    },
    [],
  );

  const downloadRawPage = async (url: string, pageNumber: number) => {
    requestSequence.current += 1;
    const requestId = requestSequence.current;
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    setLoading(true);
    setDownloadError("");

    try {
      const requestUrl = new URL(url, window.location.origin);
      if (
        requestUrl.origin !== window.location.origin ||
        requestUrl.pathname !== "/api/export"
      ) {
        throw new Error("The export URL is not a same-origin API route.");
      }

      const response = await fetch(
        `${requestUrl.pathname}${requestUrl.search}`,
        {
          cache: "no-store",
          redirect: "error",
          signal: controller.signal,
        },
      );
      if (requestId !== requestSequence.current) return;
      if (!response.ok) {
        throw new Error("The export request failed.");
      }
      if (
        response.url &&
        new URL(response.url, window.location.origin).origin !==
          window.location.origin
      ) {
        throw new Error("The export response redirected off this site.");
      }

      const hasMoreHeader = response.headers.get("X-Export-Has-More");
      const recordCount = response.headers.get("X-Export-Record-Count");
      if (
        (hasMoreHeader !== "true" && hasMoreHeader !== "false") ||
        recordCount === null ||
        !/^\d+$/.test(recordCount)
      ) {
        throw new Error(
          "The export did not include page-completeness metadata; no file was downloaded.",
        );
      }

      const hasMore = hasMoreHeader === "true";
      const nextPath = hasMore
        ? getNextPagePath(response.headers.get("Link"), requestUrl.href)
        : null;
      if (hasMore && !nextPath) {
        throw new Error(
          "More export rows exist, but no safe next-page link was provided.",
        );
      }

      const blob = await response.blob();
      if (requestId !== requestSequence.current) return;

      downloadBlob(blob, format, pageNumber);
      setDownloadedPages(pageNumber);
      setNextPageUrl(nextPath);
      setProgressMessage(
        hasMore
          ? `Page ${pageNumber} downloaded (${Number(recordCount).toLocaleString()} rows). More data is available; download page ${pageNumber + 1} to continue.`
          : `Page ${pageNumber} downloaded (${Number(recordCount).toLocaleString()} rows). No additional matching rows were reported at request time.`,
      );
    } catch {
      if (requestId !== requestSequence.current || controller.signal.aborted) {
        return;
      }
      setDownloadError(
        "The page could not be downloaded safely. Your current filters are unchanged; retry the export.",
      );
    } finally {
      if (requestId === requestSequence.current) {
        setLoading(false);
        activeRequest.current = null;
      }
    }
  };

  const handleExport = async () => {
    resetPaginationState();
    setLoading(true);

    const params = new URLSearchParams();
    if (province) params.set("province", province);
    params.set("format", format);
    params.set("granularity", granularity);
    if (!isAggregated) {
      params.set("page_size", String(RAW_EXPORT_PAGE_SIZE));
    }

    // Calculate date range
    const now = new Date();
    if (dateRange !== "all") {
      const days = DATE_RANGE_DAYS[dateRange]!;
      const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      params.set("start_date", start.toISOString());
    }

    const url = `/api/export?${params.toString()}`;
    if (!isAggregated) {
      await downloadRawPage(url, 1);
      return;
    }

    setLoading(true);
    window.location.href = url;
    window.setTimeout(() => setLoading(false), 1000);
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
            onChange={(e) => {
              resetPaginationState();
              setProvince(e.target.value);
            }}
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
            onChange={(e) => {
              resetPaginationState();
              setDateRange(e.target.value as DateRange);
            }}
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
          onChange={(e) => {
            resetPaginationState();
            setGranularity(e.target.value as Granularity);
          }}
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
            onClick={() => {
              resetPaginationState();
              setFormat("csv");
            }}
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
            onClick={() => {
              resetPaginationState();
              setFormat("json");
            }}
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
        {loading
          ? isAggregated
            ? "Preparing..."
            : "Downloading page..."
          : "Download Data"}
      </button>

      {!isAggregated && progressMessage && (
        <p role="status" className="mt-3 text-sm text-muted-foreground">
          {progressMessage} Pages are separate requests, not a
          transactionally-consistent snapshot.
        </p>
      )}
      {!isAggregated && downloadError && (
        <p role="alert" className="mt-3 text-sm text-red-600 dark:text-red-400">
          {downloadError}
        </p>
      )}
      {!isAggregated && nextPageUrl && (
        <button
          type="button"
          onClick={() => void downloadRawPage(nextPageUrl, downloadedPages + 1)}
          disabled={loading}
          className="mt-3 w-full rounded-lg border border-blue-600 px-4 py-2 font-medium text-blue-700 transition-colors hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50 dark:text-blue-300 dark:hover:bg-slate-700"
        >
          {loading
            ? "Downloading page..."
            : `Download next page (${downloadedPages + 1})`}
        </button>
      )}

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
