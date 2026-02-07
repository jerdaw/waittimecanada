import { Hospital } from "@/app/api/hospitals/route";
import { clsx } from "clsx";
import { AccessBurdenEstimator } from "./AccessBurdenEstimator";
import { BenchmarkCard } from "./BenchmarkCard";
import { TemporalPatterns } from "./TemporalPatterns";
import { calculateDistance } from "@/utils/distance";

interface ExpandedCardDetailsProps {
  hospital: Hospital;
  userLocation?: { lat: number; lon: number } | null;
}

export function ExpandedCardDetails({ hospital, userLocation }: ExpandedCardDetailsProps) {
  // Format dates
  const updatedDate = hospital.last_updated ? new Date(hospital.last_updated) : null;
  const timeString = updatedDate ? updatedDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : "--";

  const isLive = updatedDate && (new Date().getTime() - updatedDate.getTime() < 30 * 60 * 1000);

  // Calculate distance
  const distance = userLocation
    ? calculateDistance(userLocation.lat, userLocation.lon, hospital.latitude, hospital.longitude)
    : null;

  // Methodology labels
  const getMethodologyLabel = () => {
    if (hospital.province === "QC") return "Registration to Doctor";
    return "Triage to Doctor";
  };

  return (
    <div className="mt-4 pt-4 border-t border-border/30 animate-in fade-in slide-in-from-top-2 duration-300">
      {/* Stats Row */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gradient-to-br from-muted/50 to-muted/30 p-3 rounded-xl border border-border/30">
          <span className="text-[10px] uppercase text-muted-foreground font-semibold tracking-wider block mb-1">Metric</span>
          <div className="text-xs font-medium text-foreground">{getMethodologyLabel()}</div>
        </div>
        <div className="bg-gradient-to-br from-muted/50 to-muted/30 p-3 rounded-xl border border-border/30">
          <span className="text-[10px] uppercase text-muted-foreground font-semibold tracking-wider block mb-1">Status</span>
          <div className="text-xs font-medium text-foreground flex items-center gap-1.5">
            <span className={clsx(
              "w-2 h-2 rounded-full",
              isLive ? "bg-success" : "bg-warning"
            )} />
            {isLive ? "Live Data" : "Stale Data"}
          </div>
        </div>
      </div>

      {/* Telehealth Info */}
      <div className="mb-4 text-xs bg-gradient-to-r from-accent/5 to-transparent p-3 rounded-xl border border-accent/20">
        <div className="font-semibold text-accent mb-1 flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
          </div>
          Need medical advice?
        </div>
        <p className="text-muted-foreground ml-8">
          Call <span className="font-bold text-foreground">{hospital.telehealth_number || "811"}</span> to speak with a registered nurse 24/7.
        </p>
      </div>

      {/* Access Burden Estimator - Only show if user location is available */}
      {userLocation && distance && distance > 0 && (
        <div className="mb-4">
          <AccessBurdenEstimator
            distanceKm={distance}
            province={hospital.province}
            hospitalType="urban" // Could be enhanced with hospital.hospital_type field
          />
        </div>
      )}

      <div className="mb-4">
        <BenchmarkCard hospital={hospital} />
      </div>

      <div className="mb-4">
        <TemporalPatterns hospitalId={hospital.id} />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <a 
          href={`https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex flex-col items-center justify-center gap-1.5 p-3 bg-primary/5 hover:bg-primary/10 text-primary rounded-xl transition-all duration-200 group border border-primary/10 hover:border-primary/20"
          onClick={(e) => e.stopPropagation()}
        >
          <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <span className="text-[10px] font-semibold">Directions</span>
        </a>
        
        <a 
          href={`tel:${hospital.telehealth_number?.replace(/\D/g, '') || '811'}`}
          className="flex flex-col items-center justify-center gap-1.5 p-3 bg-muted/50 hover:bg-muted text-foreground rounded-xl transition-all duration-200 group border border-border/30 hover:border-border"
          onClick={(e) => e.stopPropagation()}
        >
          <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
          <span className="text-[10px] font-semibold">Call Health Info</span>
        </a>
      </div>

      <div className="mt-4 text-[10px] text-center text-muted-foreground">
        Last updated: {timeString}
      </div>
    </div>
  );
}
