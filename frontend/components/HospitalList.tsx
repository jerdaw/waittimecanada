import { Hospital } from "@/app/api/hospitals/route";
import { FixedSizeList as List } from "react-window";
import AutoSizer from "react-virtualized-auto-sizer";
import { clsx } from "clsx";
import { HospitalCardSkeleton } from "./skeletons/HospitalCardSkeleton";

import { calculateDistance } from "@/utils/distance";

interface HospitalListProps {
  hospitals: Hospital[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  className?: string;
  loading?: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  userLocation?: { lat: number; lon: number } | null;
  sortByDistance?: boolean;
  onSortChange?: (enabled: boolean) => void;
  onRequestLocation?: () => void;
}

// Helper to determine status color
function getStatusColor(minutes: number | undefined) {
  if (minutes === undefined) return "bg-gray-500";
  if (minutes < 60) return "bg-emerald-500";
  if (minutes < 120) return "bg-amber-500";
  return "bg-red-600";
}

function formatWaitTime(minutes: number | undefined) {
  if (minutes === undefined) return "--";
  return Math.round(minutes).toString();
}

function formatDistance(dist: number) {
  if (dist < 1) return `${(dist * 1000).toFixed(0)}m`;
  return `${dist.toFixed(1)}km`;
}

// Helper to determine if data is fresh (< 30 mins)
function isRecent(dateStr: string | undefined | null) {
  if (!dateStr) return false;
  const updated = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - updated.getTime();
  return diffMs < 30 * 60 * 1000; // 30 mins
}

export function HospitalList({
  hospitals,
  selectedId,
  onSelect,
  className,
  loading = false,
  searchQuery = "",
  onSearchChange,
  userLocation,
  sortByDistance,
  onSortChange,
  onRequestLocation,
}: HospitalListProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Row = ({ index, style }: { index: number; style: any }) => {
    if (loading) {
      return (
        <div style={style}>
          <HospitalCardSkeleton />
        </div>
      );
    }

    const hospital = hospitals[index];
    const isSelected = hospital.id === selectedId;
    const color = getStatusColor(hospital.current_wait_time);
    const showLiveBadge = isRecent(hospital.last_updated);
    
    // Calculate distance if user location is available
    const distance = userLocation ? calculateDistance(
      userLocation.lat, userLocation.lon, 
      hospital.lat, hospital.lon
    ) : null;

    return (
      <div style={style} className="px-4 py-2">
        <button
          onClick={() => onSelect(hospital.id)}
          className={clsx(
            "w-full text-left p-4 rounded-xl border transition-all duration-200 group flex items-start justify-between gap-4",
            isSelected
              ? "bg-primary/5 border-primary shadow-sm"
              : "bg-card border-border hover:border-primary/50 hover:shadow-sm"
          )}
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3
                className={clsx(
                  "font-semibold truncate pr-2",
                  isSelected ? "text-primary" : "text-card-foreground group-hover:text-primary"
                )}
              >
                {hospital.name}
              </h3>
              {showLiveBadge && (
                <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-500/10 px-1.5 py-0.5 rounded-full border border-emerald-500/20">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                  </span>
                  LIVE
                </span>
              )}
            </div>
            <div className="text-sm text-muted-foreground truncate flex items-center gap-2">
              <span>{hospital.city}, {hospital.province}</span>
              {distance !== null && (
                <span className="text-xs bg-muted px-1.5 py-0.5 rounded-md font-medium">
                  📍 {formatDistance(distance)}
                </span>
              )}
            </div>
            {/* Added details for larger cards */}
            {isSelected && (
              <div className="mt-2 text-xs text-muted-foreground animate-in slide-in-from-top-1 fade-in duration-200">
                <p>Updated {new Date(hospital.last_updated || "").toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                {hospital.telehealth_number && <p className="mt-1">📞 {hospital.telehealth_number}</p>}
              </div>
            )}
          </div>

          <div className="flex flex-col items-end flex-shrink-0">
            <div className={clsx("flex items-center gap-1.5 px-2.5 py-1 rounded-full text-white text-sm font-bold shadow-sm", color)}>
              <span>{formatWaitTime(hospital.current_wait_time)}</span>
              <span className="text-xs font-medium opacity-90">min</span>
            </div>
          </div>
        </button>
      </div>
    );
  };

  return (
    <div className={clsx("h-full bg-muted/30 flex flex-col", className)}>
      {/* Search Header */}
      <div className="p-4 bg-background border-b border-border shadow-sm z-10 space-y-3">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search by name or city..."
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-muted/50 focus:bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200 outline-none"
            value={searchQuery}
            onChange={(e) => onSearchChange?.(e.target.value)}
          />
        </div>

        {/* Sort Controls - Only show if functions are provided */}
        {onSortChange && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide">
             <button
              onClick={() => onSortChange(false)}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap",
                !sortByDistance
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              Default Sort
            </button>
            <button
              onClick={() => {
                if (!userLocation && onRequestLocation) {
                  onRequestLocation();
                } else {
                  onSortChange(true);
                }
              }}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5",
                sortByDistance
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              <span>Verify Location</span>
              <span>Near Me</span>
            </button>
          </div>
        )}
      </div>

      <div className="flex-1">
        {!loading && hospitals.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8 text-center">
            <p>No hospitals found matching "{searchQuery}"</p>
            <button 
              onClick={() => onSearchChange?.("")}
              className="mt-2 text-primary hover:underline text-sm"
            >
              Clear search
            </button>
          </div>
        ) : (
          <AutoSizer>
            {({ height, width }) => (
              <List
                height={height}
                itemCount={loading ? 10 : hospitals.length}
                itemSize={100} // Height of each card + padding
                width={width}
                initialScrollOffset={
                  !loading && selectedId
                    ? Math.max(0, hospitals.findIndex((h) => h.id === selectedId) * 100 - height / 2 + 50)
                    : 0
                }
              >
                {Row}
              </List>
            )}
          </AutoSizer>
        )}
      </div>
    </div>
  );
}
