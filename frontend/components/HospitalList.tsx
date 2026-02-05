import { Hospital } from "@/app/api/hospitals/route";
import { clsx } from "clsx";
import { HospitalCardSkeleton } from "./skeletons/HospitalCardSkeleton";
import { ExpandedCardDetails } from "./ExpandedCardDetails";
import { calculateDistance } from "@/utils/distance";
import { useState, useRef, useEffect } from "react";
import { isRecent } from "@/utils/date";

interface HospitalListProps {
  hospitals: Hospital[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  className?: string;
  loading?: boolean;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  userLocation?: { lat: number; lon: number } | null;
  onRequestLocation?: () => void;
  showLiveOnly?: boolean;
  onToggleLiveOnly?: (enabled: boolean) => void;
}

// Helper to determine status color
function getStatusColor(minutes: number | undefined) {
  if (minutes === undefined) return "bg-muted-foreground";
  if (minutes < 60) return "bg-success";
  if (minutes < 120) return "bg-warning";
  return "bg-danger";
}

function formatWaitTime(minutes: number | undefined) {
  if (minutes === undefined) return "--";
  return Math.round(minutes).toString();
}

function formatDistance(dist: number) {
  if (dist < 1) return `${(dist * 1000).toFixed(0)}m`;
  return `${dist.toFixed(1)}km`;
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
  onRequestLocation,
  showLiveOnly = false,
  onToggleLiveOnly,
}: HospitalListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Scroll to selected item if it changes from outside (e.g. map click)
  useEffect(() => {
    if (selectedId && listRef.current) {
      const el = document.getElementById(`hospital-card-${selectedId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        setExpandedId(selectedId);
      }
    }
  }, [selectedId]);

  const handleCardClick = (id: string) => {
    onSelect(id);
    setExpandedId(expandedId === id ? null : id);
  };

  const displayedHospitals = hospitals;

  return (
    <div className={clsx("h-full flex flex-col", className)}>
      {/* Compact Filter Bar */}
      <div className="p-4 bg-background/80 backdrop-blur-sm border-b border-border/50 z-10 shrink-0">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Live Only Toggle */}
          {onToggleLiveOnly && (
            <button
              onClick={() => onToggleLiveOnly(!showLiveOnly)}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 border",
                showLiveOnly
                  ? "bg-success/10 border-success/30 text-success"
                  : "bg-background border-border text-muted-foreground hover:bg-muted/50"
              )}
            >
              <span className="relative flex h-1.5 w-1.5">
                <span className={clsx(
                  "absolute inline-flex h-full w-full rounded-full opacity-75",
                  showLiveOnly ? "animate-ping bg-success" : "bg-muted-foreground"
                )} />
                <span className={clsx(
                  "relative inline-flex rounded-full h-1.5 w-1.5",
                  showLiveOnly ? "bg-success" : "bg-muted-foreground"
                )} />
              </span>
              Live Only
            </button>
          )}

          {/* Results count */}
          <span className="text-xs text-muted-foreground ml-auto pr-1">
            {displayedHospitals.length} results
          </span>
        </div>
      </div>

      {/* Scrollable List */}
      <div className="flex-1 overflow-y-auto" ref={listRef}>
        {!loading && displayedHospitals.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-6 text-center min-h-[150px]">
            <svg className="w-8 h-8 mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <p className="text-sm font-medium">No hospitals found</p>
            {searchQuery && (
              <button 
                onClick={() => onSearchChange?.("")}
                className="mt-2 px-3 py-1.5 text-xs font-medium text-primary hover:bg-primary/5 rounded-lg transition-colors"
              >
                Clear search
              </button>
            )}
          </div>
        ) : loading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <HospitalCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="p-4 space-y-2">
            {displayedHospitals.map((hospital) => {
              const isSelected = hospital.id === selectedId;
              const isExpanded = hospital.id === expandedId;
              const color = getStatusColor(hospital.current_wait_time);
              const showLiveBadge = isRecent(hospital.last_updated);
              
              // Calculate distance if user location is available
              const distance = userLocation ? calculateDistance(
                userLocation.lat, userLocation.lon, 
                hospital.latitude, hospital.longitude
              ) : null;

              return (
                <div 
                  key={hospital.id} 
                  id={`hospital-card-${hospital.id}`}
                  className={clsx(
                    "rounded-xl border transition-all duration-200 overflow-hidden",
                    isSelected || isExpanded
                      ? "bg-card border-primary/50 ring-1 ring-primary/20 shadow-lg translate-y-[-1px]"
                      : "bg-card/50 border-border/30 hover:bg-card hover:border-border/50 hover:shadow-sm"
                  )}
                >
                  {/* Compact Card Row */}
                  <button
                    onClick={() => handleCardClick(hospital.id)}
                    className="w-full text-left p-4 flex items-center gap-4"
                  >
                    {/* Status Indicator */}
                    <div className={clsx("w-1.5 h-8 rounded-full shrink-0", color)} />

                    {/* Name & Location */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className={clsx(
                          "font-medium text-sm truncate",
                          (isSelected || isExpanded) ? "text-primary" : "text-foreground"
                        )}>
                          {hospital.name}
                        </h3>
                        {showLiveBadge && (
                          <span className="shrink-0 flex items-center gap-0.5 text-[9px] font-bold text-success bg-success/10 px-1 py-0.5 rounded">
                            <span className="w-1 h-1 rounded-full bg-success animate-pulse" />
                            LIVE
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-2">
                        <span className="truncate">{hospital.city}</span>
                        {distance !== null && (
                          <span className="shrink-0 text-[10px] bg-muted/50 px-1 py-0.5 rounded font-medium">
                            {formatDistance(distance)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Wait Time */}
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="text-right">
                        <span className="text-lg font-bold tabular-nums">{formatWaitTime(hospital.current_wait_time)}</span>
                        <span className="text-xs text-muted-foreground ml-0.5">min</span>
                      </div>
                      <svg 
                        className={clsx(
                          "w-4 h-4 text-muted-foreground transition-transform duration-200",
                          isExpanded && "rotate-180"
                        )} 
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  {/* Expanded Content */}
                  <div 
                    className={clsx(
                      "grid transition-[grid-template-rows] duration-300 ease-out",
                      isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                    )}
                  >
                    <div className="overflow-hidden px-3 pb-3">
                      <ExpandedCardDetails hospital={hospital} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
