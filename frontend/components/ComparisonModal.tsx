"use client";

import { useEffect, useState } from "react";
import { DivergenceWarning } from "./DivergenceWarning";

interface Hospital {
  id: string;
  name: string;
  province: string;
  city: string;
  wait_time: number;
  last_updated: string;
  methodology: {
    metric_family: string;
    start_event: string;
    end_event: string;
    statistic_type: string;
  };
}

interface ComparisonData {
  hospital_a: Hospital;
  hospital_b: Hospital;
  comparable: boolean;
  divergence_brief: string | null;
  comparison_timestamp: string;
}

interface ComparisonModalProps {
  hospitalAId: string;
  hospitalBId: string;
  onClose: () => void;
}

function getWaitTimeColor(minutes: number): string {
  if (minutes < 60) return "text-emerald-600";
  if (minutes < 120) return "text-amber-600";
  return "text-red-600";
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
}

function MethodologyField({
  label,
  valueA,
  valueB,
}: {
  label: string;
  valueA: string;
  valueB: string;
}) {
  const matches = valueA === valueB;

  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-200 last:border-0">
      <span className="text-sm font-medium text-slate-600">{label}</span>
      <div className="flex items-center gap-2">
        <code
          className={`px-2 py-1 rounded text-xs font-mono ${matches ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}
        >
          {valueA}
        </code>
        <span className={matches ? "text-emerald-500" : "text-amber-500"}>
          {matches ? "=" : "≠"}
        </span>
        <code
          className={`px-2 py-1 rounded text-xs font-mono ${matches ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}
        >
          {valueB}
        </code>
      </div>
    </div>
  );
}

export function ComparisonModal({
  hospitalAId,
  hospitalBId,
  onClose,
}: ComparisonModalProps) {
  const [data, setData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchComparison() {
      try {
        const response = await fetch(
          `/api/compare?a=${hospitalAId}&b=${hospitalBId}`
        );
        const result = await response.json();

        if (!result.success) {
          throw new Error(result.message || "Failed to fetch comparison");
        }

        setData(result.data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
        setLoading(false);
      }
    }

    fetchComparison();
  }, [hospitalAId, hospitalBId]);

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div className="bg-white rounded-2xl p-8 max-w-2xl w-full mx-4 shadow-2xl">
          <div className="flex items-center justify-center gap-3">
            <div className="w-6 h-6 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-slate-600">Loading comparison...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              Comparison Failed
            </h3>
            <p className="text-slate-600 mb-4">{error || "Unknown error"}</p>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-slate-900">
            Hospital Comparison
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-slate-100 transition-colors"
            aria-label="Close"
          >
            <svg
              className="w-5 h-5 text-slate-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Divergence Warning (if applicable) */}
          {!data.comparable && data.divergence_brief && (
            <DivergenceWarning message={data.divergence_brief} variant="banner" />
          )}

          {/* Comparable indicator */}
          {data.comparable && (
            <div className="rounded-xl border-2 border-emerald-300 bg-emerald-50 p-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0">
                  <svg
                    className="w-6 h-6 text-emerald-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-emerald-900 text-sm mb-1">
                    Directly Comparable
                  </h4>
                  <p className="text-emerald-800 text-sm">
                    These hospitals use identical methodologies. Direct comparison is
                    statistically valid.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Side-by-side comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Hospital A */}
            <div className="rounded-xl border-2 border-slate-200 bg-slate-50 p-6">
              <h3 className="font-bold text-slate-900 text-lg mb-1">
                {data.hospital_a.name}
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                {data.hospital_a.city}, {data.hospital_a.province}
              </p>

              <div className="bg-white rounded-lg p-4 mb-4">
                <div className="text-center">
                  <div
                    className={`text-4xl font-bold ${getWaitTimeColor(data.hospital_a.wait_time)}`}
                  >
                    {Math.round(data.hospital_a.wait_time)}
                    <span className="text-lg text-slate-500 font-normal ml-1">
                      min
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Updated {formatRelativeTime(data.hospital_a.last_updated)}
                  </p>
                </div>
              </div>

              <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-2">
                Methodology
              </div>
              <div className="space-y-1 text-sm">
                <div>
                  <span className="font-medium">Metric:</span>{" "}
                  {data.hospital_a.methodology.metric_family}
                </div>
                <div>
                  <span className="font-medium">Start:</span>{" "}
                  {data.hospital_a.methodology.start_event}
                </div>
                <div>
                  <span className="font-medium">End:</span>{" "}
                  {data.hospital_a.methodology.end_event}
                </div>
                <div>
                  <span className="font-medium">Stat:</span>{" "}
                  {data.hospital_a.methodology.statistic_type}
                </div>
              </div>
            </div>

            {/* Hospital B */}
            <div className="rounded-xl border-2 border-slate-200 bg-slate-50 p-6">
              <h3 className="font-bold text-slate-900 text-lg mb-1">
                {data.hospital_b.name}
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                {data.hospital_b.city}, {data.hospital_b.province}
              </p>

              <div className="bg-white rounded-lg p-4 mb-4">
                <div className="text-center">
                  <div
                    className={`text-4xl font-bold ${getWaitTimeColor(data.hospital_b.wait_time)}`}
                  >
                    {Math.round(data.hospital_b.wait_time)}
                    <span className="text-lg text-slate-500 font-normal ml-1">
                      min
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Updated {formatRelativeTime(data.hospital_b.last_updated)}
                  </p>
                </div>
              </div>

              <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-2">
                Methodology
              </div>
              <div className="space-y-1 text-sm">
                <div>
                  <span className="font-medium">Metric:</span>{" "}
                  {data.hospital_b.methodology.metric_family}
                </div>
                <div>
                  <span className="font-medium">Start:</span>{" "}
                  {data.hospital_b.methodology.start_event}
                </div>
                <div>
                  <span className="font-medium">End:</span>{" "}
                  {data.hospital_b.methodology.end_event}
                </div>
                <div>
                  <span className="font-medium">Stat:</span>{" "}
                  {data.hospital_b.methodology.statistic_type}
                </div>
              </div>
            </div>
          </div>

          {/* Methodology comparison table */}
          <div className="bg-slate-50 rounded-xl p-6">
            <h4 className="font-semibold text-slate-900 mb-4">
              Methodology Comparison
            </h4>
            <div className="bg-white rounded-lg p-4 space-y-2">
              <MethodologyField
                label="Metric Family"
                valueA={data.hospital_a.methodology.metric_family}
                valueB={data.hospital_b.methodology.metric_family}
              />
              <MethodologyField
                label="Start Event"
                valueA={data.hospital_a.methodology.start_event}
                valueB={data.hospital_b.methodology.start_event}
              />
              <MethodologyField
                label="End Event"
                valueA={data.hospital_a.methodology.end_event}
                valueB={data.hospital_b.methodology.end_event}
              />
              <MethodologyField
                label="Statistic Type"
                valueA={data.hospital_a.methodology.statistic_type}
                valueB={data.hospital_b.methodology.statistic_type}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t border-slate-200 px-6 py-4 flex justify-between items-center">
          <a
            href="/methods"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Learn more about methodologies →
          </a>
          <button
            onClick={onClose}
            className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
