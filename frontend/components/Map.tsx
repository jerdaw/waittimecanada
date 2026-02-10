"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import MapGL, {
  Marker,
  Popup,
  NavigationControl,
  Source,
  Layer,
  type LayerProps,
} from "react-map-gl";
import type { Hospital } from "@/app/api/hospitals/route";
import { ComparisonModal } from "./ComparisonModal";
import { DivergenceWarning } from "./DivergenceWarning";
import { TrendChart } from "./TrendChart";
import { BenchmarkCard } from "./BenchmarkCard";
import { EquityLayerToggle } from "./EquityLayerToggle";
import { EquityLegend } from "./EquityLegend";
import {
  EQUITY_QUINTILE_COLORS,
  type EquityFeatureCollection,
  type EquityLayerApiResponse,
  type EquityLayerMetadata,
} from "@/utils/equity";
import "mapbox-gl/dist/mapbox-gl.css";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

// Design tokens
const colors = {
  good: "#059669", // emerald-600
  moderate: "#D97706", // amber-600
  busy: "#DC2626", // red-600
  unknown: "#6B7280", // gray-500
  primary: "#2563EB", // blue-600
};

const EQUITY_FILL_LAYER: LayerProps = {
  id: "equity-fill",
  type: "fill",
  paint: {
    "fill-color": [
      "match",
      ["get", "income_quintile"],
      1,
      EQUITY_QUINTILE_COLORS[1],
      2,
      EQUITY_QUINTILE_COLORS[2],
      3,
      EQUITY_QUINTILE_COLORS[3],
      4,
      EQUITY_QUINTILE_COLORS[4],
      5,
      EQUITY_QUINTILE_COLORS[5],
      "#CBD5E1",
    ] as any,
    "fill-opacity": 0.24,
  },
};

const EQUITY_OUTLINE_LAYER: LayerProps = {
  id: "equity-outline",
  type: "line",
  paint: {
    "line-color": "#ffffff",
    "line-width": 0.6,
    "line-opacity": 0.45,
  },
};

// Get marker color based on wait time
function getWaitTimeColor(minutes: number | undefined): string {
  if (!minutes && minutes !== 0) return colors.unknown;
  if (minutes < 60) return colors.good;
  if (minutes < 120) return colors.moderate;
  return colors.busy;
}

// Get status label
function getWaitTimeStatus(minutes: number | undefined): string {
  if (!minutes && minutes !== 0) return "No data";
  if (minutes < 60) return "Short wait";
  if (minutes < 120) return "Moderate wait";
  return "Long wait";
}

// Format relative time
function formatRelativeTime(dateString: string | undefined): string {
  if (!dateString) return "Unknown";
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

// Format methodology for display
function formatMethodology(hospital: Hospital): string {
  if (!hospital.metric_family) return "";

  const parts = [];

  // Start event
  if (hospital.start_event) {
    const startMap: Record<string, string> = {
      TRIAGE: "Triage",
      REGISTRATION: "Registration",
      DOOR: "Door",
      UNKNOWN: "Arrival",
    };
    parts.push(startMap[hospital.start_event] || hospital.start_event);
  }

  // Arrow
  parts.push("→");

  // End event
  if (hospital.end_event) {
    const endMap: Record<string, string> = {
      PHYSICIAN: "Physician",
      PROVIDER: "Provider",
      DISCHARGE: "Discharge",
      FIRST_ASSESSMENT: "First Assessment",
    };
    parts.push(endMap[hospital.end_event] || hospital.end_event);
  }

  return parts.join(" ");
}

// Format statistic type for display
function formatStatistic(statType: string | undefined): string {
  if (!statType) return "";

  const statMap: Record<string, string> = {
    P90: "90th percentile",
    MEAN: "Average",
    MEDIAN: "Median",
    P95: "95th percentile",
    POINT_ESTIMATE: "Current estimate",
    ROLLING_AVG: "Rolling average",
    ALGORITHMIC: "Calculated estimate",
  };

  return statMap[statType] || statType;
}

// Custom marker component
function HospitalMarker({
  waitTime,
  isSelected,
  isSelectedForComparison,
}: {
  waitTime: number | undefined;
  isSelected: boolean;
  isSelectedForComparison?: boolean;
}) {
  const color = getWaitTimeColor(waitTime);
  const hasData = waitTime !== undefined && waitTime !== null;

  return (
    <div className="relative cursor-pointer group">
      {/* Outer ring animation for selected state */}
      {isSelected && !isSelectedForComparison && (
        <div
          className="absolute -inset-2 rounded-full animate-ping opacity-30"
          style={{ backgroundColor: color }}
        />
      )}

      {/* Checkmark for comparison selection */}
      {isSelectedForComparison && (
        <div className="absolute -top-2 -right-2 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center border-2 border-white shadow-lg z-10">
          <svg
            className="w-3 h-3 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
      )}

      {/* Main marker */}
      <div
        className={`
          relative flex items-center justify-center
          transition-all duration-200 ease-out
          ${isSelected ? "scale-125 z-50" : "group-hover:scale-110"}
        `}
      >
        {/* Pin shape */}
        <div
          className="relative flex flex-col items-center"
          style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.2))" }}
        >
          {/* Marker body */}
          <div
            className={`
              flex items-center justify-center rounded-full
              border-2 border-white
              ${hasData ? "w-10 h-10" : "w-8 h-8"}
            `}
            style={{ backgroundColor: color }}
          >
            {hasData && (
              <span className="text-white text-xs font-semibold">
                {waitTime}
              </span>
            )}
          </div>
          {/* Pin tail */}
          <div
            className="w-0 h-0 -mt-1"
            style={{
              borderLeft: "6px solid transparent",
              borderRight: "6px solid transparent",
              borderTop: `8px solid ${color}`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

// Popup component
function HospitalPopup({
  hospital,
  onClose,
}: {
  hospital: Hospital;
  onClose: () => void;
}) {
  const color = getWaitTimeColor(hospital.current_wait_time);
  const status = getWaitTimeStatus(hospital.current_wait_time);
  const hasData =
    hospital.current_wait_time !== undefined &&
    hospital.current_wait_time !== null;

  return (
    <Popup
      latitude={hospital.latitude}
      longitude={hospital.longitude}
      onClose={onClose}
      closeOnClick={false}
      closeButton={false}
      anchor="bottom"
      offset={20}
      className="hospital-popup"
    >
      <div className="w-72 bg-white rounded-xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-slate-900 text-base leading-tight truncate">
                {hospital.name}
              </h3>
              <p className="text-sm text-slate-500 mt-0.5">
                {hospital.city}, {hospital.province}
              </p>
            </div>
            <button
              onClick={onClose}
              className="ml-2 p-1 rounded-full hover:bg-slate-100 transition-colors"
              aria-label="Close"
            >
              <svg
                className="w-4 h-4 text-slate-400"
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
        </div>

        {/* Wait time display */}
        <div
          className="mx-4 mb-3 rounded-lg p-4"
          style={{ backgroundColor: `${color}10` }}
        >
          {hasData ? (
            <div className="text-center">
              <div className="flex items-baseline justify-center gap-1">
                <span className="text-3xl font-bold" style={{ color }}>
                  {Math.round(hospital.current_wait_time!)}
                </span>
                <span className="text-lg font-medium text-slate-500">min</span>
              </div>
              <div className="text-sm font-medium mt-1" style={{ color }}>
                {status}
              </div>
            </div>
          ) : (
            <div className="text-center py-2">
              <div className="text-slate-400 text-sm">No data available</div>
            </div>
          )}
        </div>

        {/* Trend Chart (only if we have an ID) */}
        {hospital.id && (
          <div className="px-4 mb-3">
            <TrendChart hospitalId={hospital.id} />
          </div>
        )}

        <div className="px-4 mb-3">
          <BenchmarkCard hospital={hospital} compact />
        </div>

        {/* Methodology information */}
        {hasData && hospital.metric_family && (
          <div className="px-4 pb-3 border-t border-slate-100 pt-3">
            <div className="text-xs text-slate-500 mb-1.5 font-medium">
              METHODOLOGY
            </div>
            <div className="space-y-1">
              <div className="flex items-center text-xs text-slate-600">
                <span className="font-medium mr-1">Measure:</span>
                <span>{formatMethodology(hospital)}</span>
              </div>
              {hospital.statistic_type && (
                <div className="flex items-center text-xs text-slate-600">
                  <span className="font-medium mr-1">Type:</span>
                  <span>{formatStatistic(hospital.statistic_type)}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Telehealth information */}
        {hospital.telehealth_name && hospital.telehealth_number && (
          <div className="px-4 pb-3 border-t border-slate-100 pt-3">
            <div className="flex items-start gap-2">
              <div className="flex-shrink-0 mt-0.5">
                <svg
                  className="w-4 h-4 text-blue-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <div className="text-xs text-slate-600 mb-1">
                  <span className="font-medium">Need medical advice?</span>
                </div>
                <div className="text-xs text-slate-900">
                  Call{" "}
                  <span className="font-semibold">
                    {hospital.telehealth_name}
                  </span>
                </div>
                <a
                  href={`tel:${hospital.telehealth_number}`}
                  className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-700 mt-1"
                >
                  {hospital.telehealth_number}
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="px-4 pb-3 border-t border-slate-100 pt-3 grid grid-cols-2 gap-2">
          <a
            href={`https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex flex-col items-center justify-center gap-1 p-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors group"
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
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.447 2.724A1 1 0 0121 18.382V7.618a1 1 0 00-.553-.894L15 7m0 13V7m0 0a2 2 0 012-2h.01M9 17v5a2 2 0 01-2-2h.01M9 17H5"
              />
            </svg>
            <span className="text-[10px] font-semibold">Directions</span>
          </a>

          <a
            href={`tel:${hospital.telehealth_number?.replace(/\D/g, "") || "811"}`}
            className="flex flex-col items-center justify-center gap-1 p-2 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-lg transition-colors"
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
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
              />
            </svg>
            <span className="text-[10px] font-semibold">Call Health Info</span>
          </a>
        </div>

        {/* Footer */}
        <div className="px-4 pb-4 flex items-center justify-between text-xs text-slate-500">
          <span>Updated {formatRelativeTime(hospital.last_updated)}</span>
          <div className="flex items-center gap-1">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="capitalize">{status.toLowerCase()}</span>
          </div>
        </div>
      </div>
    </Popup>
  );
}

// Data freshness indicator
function DataFreshnessIndicator({
  lastUpdate,
  isStale,
}: {
  lastUpdate: string | null;
  isStale: boolean;
}) {
  return (
    <div
      className={`
      flex items-center gap-2 px-3 py-2 rounded-lg text-sm
      ${isStale ? "bg-amber-50 text-amber-700" : "bg-white text-slate-600"}
      shadow-sm border border-slate-200
    `}
    >
      <div
        className={`w-2 h-2 rounded-full ${isStale ? "bg-amber-500 animate-pulse" : "bg-emerald-500"}`}
      />
      <span>
        {isStale
          ? "Data may be stale"
          : `Updated ${formatRelativeTime(lastUpdate ?? undefined)}`}
      </span>
    </div>
  );
}

// Legend component
function MapLegend() {
  const items = [
    { color: colors.good, label: "< 60 min", description: "Short wait" },
    { color: colors.moderate, label: "60-120 min", description: "Moderate" },
    { color: colors.busy, label: "> 120 min", description: "Long wait" },
  ];

  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-4 border border-slate-200">
      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
        Wait Time
      </h4>
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-3">
            <div
              className="w-4 h-4 rounded-full border-2 border-white shadow-sm flex-shrink-0"
              style={{ backgroundColor: item.color }}
            />
            <div className="flex items-center justify-between flex-1 min-w-0">
              <span className="text-sm text-slate-700">{item.label}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Stats badge
function StatsBadge({ count, label }: { count: number; label: string }) {
  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg px-4 py-3 border border-slate-200">
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold text-slate-900">{count}</span>
        <span className="text-sm text-slate-500">{label}</span>
      </div>
    </div>
  );
}

// Loading skeleton
function MapSkeleton() {
  return (
    <div className="flex h-screen items-center justify-center bg-slate-100">
      <div className="text-center">
        <div className="inline-flex items-center gap-3">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-lg text-slate-600">Loading hospitals...</span>
        </div>
      </div>
    </div>
  );
}

// Error display
function MapError({ message }: { message: string }) {
  return (
    <div className="flex h-screen items-center justify-center bg-slate-50">
      <div className="max-w-md text-center p-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
          <svg
            className="w-8 h-8 text-red-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">
          Unable to load map
        </h2>
        <p className="text-slate-600">{message}</p>
      </div>
    </div>
  );
}

// Missing token display
function MissingTokenError() {
  return (
    <div className="flex h-screen items-center justify-center bg-slate-50">
      <div className="max-w-md text-center p-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-100 flex items-center justify-center">
          <svg
            className="w-8 h-8 text-amber-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
            />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">
          Mapbox token required
        </h2>
        <p className="text-slate-600 mb-4">
          Add your Mapbox token to view the interactive map.
        </p>
        <code className="inline-block bg-slate-100 px-3 py-2 rounded text-sm text-slate-700">
          NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxx
        </code>
      </div>
    </div>
  );
}

interface MapProps {
  hospitals: Hospital[];
  province?: string;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  lastUpdate: string | null;
  isStale: boolean;
  loading: boolean;
  error: string | null;
  className?: string;
  userLocation?: { lat: number; lon: number } | null;
}

// Main Map component
export default function Map({
  hospitals,
  province = "ON",
  selectedId,
  onSelect,
  lastUpdate,
  isStale,
  loading,
  error,
  className,
  userLocation,
}: MapProps) {
  // Comparison mode state
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<
    Hospital[]
  >([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [showEquityLayer, setShowEquityLayer] = useState(false);
  const [equityStatus, setEquityStatus] = useState<
    "idle" | "loading" | "ready" | "unavailable" | "error"
  >("idle");
  const [equityError, setEquityError] = useState<string | null>(null);
  const [equityDataByProvince, setEquityDataByProvince] = useState<
    Record<string, EquityFeatureCollection>
  >({});
  const [equityMetadataByProvince, setEquityMetadataByProvince] = useState<
    Record<string, EquityLayerMetadata>
  >({});

  const normalizedProvince = province.toUpperCase();
  const activeEquityData = equityDataByProvince[normalizedProvince] ?? null;
  const activeEquityMetadata =
    equityMetadataByProvince[normalizedProvince] ?? null;

  // Find selected hospital object
  const selectedHospital = useMemo(
    () => hospitals.find((h) => h.id === selectedId) || null,
    [hospitals, selectedId],
  );

  // Handle marker click
  const handleMarkerClick = useCallback(
    (hospital: Hospital) => {
      if (comparisonMode) {
        // In comparison mode, toggle selection
        setSelectedForComparison((prev) => {
          const isSelected = prev.some((h) => h.id === hospital.id);
          if (isSelected) {
            return prev.filter((h) => h.id !== hospital.id);
          }
          if (prev.length >= 2) {
            // Max 2 hospitals for comparison
            return prev;
          }
          return [...prev, hospital];
        });
      } else {
        // Normal mode - trigger parent select
        onSelect(hospital.id);
      }
    },
    [comparisonMode, onSelect],
  );

  // Close popup
  const handleClosePopup = useCallback(() => {
    onSelect(null);
  }, [onSelect]);

  // Toggle comparison mode
  const toggleComparisonMode = useCallback(() => {
    setComparisonMode((prev) => !prev);
    setSelectedForComparison([]);
    onSelect(null);
  }, [onSelect]);

  // Open comparison modal
  const handleCompare = useCallback(() => {
    if (selectedForComparison.length === 2) {
      setShowComparisonModal(true);
    }
  }, [selectedForComparison]);

  // Close comparison modal
  const handleCloseComparison = useCallback(() => {
    setShowComparisonModal(false);
  }, []);

  // Calculate center: user location > hospitals center > Ottawa default
  const initialViewState = useMemo(() => {
    // If user location is available, center on them with higher zoom
    if (userLocation) {
      return {
        latitude: userLocation.lat,
        longitude: userLocation.lon,
        zoom: 9, // Closer zoom when centered on user
      };
    }
    // Otherwise center on hospital data
    if (hospitals.length > 0) {
      const lats = hospitals.map((h) => h.latitude);
      const lngs = hospitals.map((h) => h.longitude);
      return {
        latitude: (Math.min(...lats) + Math.max(...lats)) / 2,
        longitude: (Math.min(...lngs) + Math.max(...lngs)) / 2,
        zoom: 5,
      };
    }
    return {
      latitude: 45.4215, // Ottawa - center of populated Canada
      longitude: -75.6972,
      zoom: 5,
    };
  }, [hospitals, userLocation]);

  useEffect(() => {
    if (!showEquityLayer) {
      setEquityStatus("idle");
      setEquityError(null);
      return;
    }

    if (activeEquityData) {
      setEquityStatus("ready");
      setEquityError(null);
      return;
    }

    let cancelled = false;

    async function loadEquityLayer() {
      setEquityStatus("loading");
      setEquityError(null);

      try {
        const response = await fetch(
          `/api/equity-layer?province=${normalizedProvince}`,
        );
        const payload = (await response.json()) as EquityLayerApiResponse;

        if (!response.ok || !payload.success) {
          if (cancelled) return;

          const errorMessage =
            "error" in payload ? payload.error : "Failed to load equity layer";
          setEquityError(errorMessage);
          setEquityStatus(response.status === 404 ? "unavailable" : "error");
          return;
        }

        if (cancelled) return;

        setEquityDataByProvince((prev) => ({
          ...prev,
          [normalizedProvince]: payload.data,
        }));
        setEquityMetadataByProvince((prev) => ({
          ...prev,
          [normalizedProvince]: payload.metadata,
        }));
        setEquityStatus("ready");
      } catch (err) {
        console.error("Failed to load equity layer:", err);
        if (cancelled) return;
        setEquityError("Failed to load equity layer. Try again shortly.");
        setEquityStatus("error");
      }
    }

    loadEquityLayer();

    return () => {
      cancelled = true;
    };
  }, [activeEquityData, normalizedProvince, showEquityLayer]);

  // Render states
  if (!MAPBOX_TOKEN) return <MissingTokenError />;
  if (loading) return <MapSkeleton />;
  if (error) return <MapError message={error} />;

  return (
    <div className={`relative h-full w-full ${className || ""}`}>
      <MapGL
        initialViewState={initialViewState}
        mapboxAccessToken={MAPBOX_TOKEN}
        mapStyle="mapbox://styles/mapbox/light-v11"
        style={{ width: "100%", height: "100%" }}
        attributionControl={false}
        onClick={() => onSelect(null)}
      >
        <NavigationControl position="bottom-right" showCompass={false} />

        {showEquityLayer &&
          activeEquityData &&
          activeEquityData.features.length > 0 && (
            <Source
              id={`equity-${normalizedProvince}`}
              type="geojson"
              data={activeEquityData as any}
            >
              <Layer {...EQUITY_FILL_LAYER} />
              <Layer {...EQUITY_OUTLINE_LAYER} />
            </Source>
          )}

        {/* Hospital markers */}
        {hospitals.map((hospital) => {
          const isSelectedForComp = selectedForComparison.some(
            (h) => h.id === hospital.id,
          );
          return (
            <Marker
              key={hospital.id}
              latitude={hospital.latitude}
              longitude={hospital.longitude}
              anchor="bottom"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                handleMarkerClick(hospital);
              }}
            >
              <HospitalMarker
                waitTime={hospital.current_wait_time}
                isSelected={selectedHospital?.id === hospital.id}
                isSelectedForComparison={isSelectedForComp}
              />
            </Marker>
          );
        })}

        {/* Selected hospital popup */}
        {selectedHospital && !comparisonMode && (
          <HospitalPopup
            hospital={selectedHospital}
            onClose={handleClosePopup}
          />
        )}
      </MapGL>

      {/* Comparison Mode UI */}
      {comparisonMode && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
          <div className="bg-white rounded-xl shadow-lg border-2 border-blue-200 p-4 min-w-80">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-900">Comparison Mode</h3>
              <button
                onClick={toggleComparisonMode}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg
                  className="w-5 h-5"
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
            <p className="text-sm text-slate-600 mb-3">
              Select 2 hospitals to compare ({selectedForComparison.length}/2
              selected)
            </p>
            {selectedForComparison.length > 0 && (
              <div className="space-y-2 mb-3">
                {selectedForComparison.map((hospital, index) => (
                  <div
                    key={hospital.id}
                    className="flex items-center justify-between bg-blue-50 rounded-lg p-2"
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center font-semibold">
                        {index + 1}
                      </span>
                      <span className="text-sm font-medium text-slate-900">
                        {hospital.name}
                      </span>
                    </div>
                    <button
                      onClick={() =>
                        setSelectedForComparison((prev) =>
                          prev.filter((h) => h.id !== hospital.id),
                        )
                      }
                      className="text-slate-400 hover:text-slate-600"
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
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
            <button
              onClick={handleCompare}
              disabled={selectedForComparison.length !== 2}
              className={`w-full py-2 rounded-lg font-medium transition-colors ${
                selectedForComparison.length === 2
                  ? "bg-blue-600 hover:bg-blue-700 text-white"
                  : "bg-slate-100 text-slate-400 cursor-not-allowed"
              }`}
            >
              Compare Hospitals
            </button>
          </div>
        </div>
      )}

      {/* Comparison Modal */}
      {showComparisonModal && selectedForComparison.length === 2 && (
        <ComparisonModal
          hospitalAId={selectedForComparison[0].id}
          hospitalBId={selectedForComparison[1].id}
          onClose={handleCloseComparison}
        />
      )}

      {/* UI Overlays */}
      <div className="absolute top-4 left-4 z-10">
        <DataFreshnessIndicator lastUpdate={lastUpdate} isStale={isStale} />
      </div>

      <div className="absolute top-16 left-4 z-10 flex max-w-[320px] flex-col gap-2">
        <EquityLayerToggle
          enabled={showEquityLayer}
          loading={equityStatus === "loading"}
          onChange={setShowEquityLayer}
        />
        {showEquityLayer &&
          (equityStatus === "unavailable" || equityStatus === "error") && (
            <div className="rounded-lg border border-amber-200 bg-amber-50/95 px-3 py-2 text-xs text-amber-800 shadow-sm">
              {equityError ?? "Equity layer is unavailable for this province."}
            </div>
          )}
      </div>

      <div className="absolute top-4 right-4 z-10">
        <StatsBadge count={hospitals.length} label="hospitals" />
      </div>

      <div className="absolute bottom-8 left-4 z-10 flex flex-col gap-3">
        {showEquityLayer &&
          activeEquityData &&
          activeEquityData.features.length > 0 && (
            <EquityLegend metadata={activeEquityMetadata ?? undefined} />
          )}
        <MapLegend />
      </div>

      {/* Navigation & Branding */}
      <div className="absolute bottom-4 right-4 z-10 flex flex-col items-end gap-2">
        {!comparisonMode && (
          <>
            <button
              onClick={toggleComparisonMode}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition-all shadow-sm flex items-center gap-2"
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
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              Compare Hospitals
            </button>
            <a
              href="/methods"
              className="bg-white/95 backdrop-blur-sm rounded-lg px-4 py-2 text-sm text-slate-700 hover:bg-white hover:text-blue-600 transition-all shadow-sm border border-slate-200 font-medium"
            >
              Understanding Methodologies →
            </a>
          </>
        )}
        <div className="bg-white/80 backdrop-blur-sm rounded-lg px-3 py-1.5 text-xs text-slate-500">
          WaitTime Canada
        </div>
      </div>
    </div>
  );
}
