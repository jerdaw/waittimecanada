"use client";

import { clsx } from "clsx";
import { useEffect, useState, useCallback } from "react";
import Map from "@/components/Map";
import { HospitalList } from "@/components/HospitalList";
import { ViewToggle, ViewMode } from "@/components/ViewToggle";
import { Header } from "@/components/Header";
import type { Hospital } from "@/app/api/hospitals/route";

import { HeroSkeleton } from "@/components/skeletons/HeroSkeleton";
import { calculateDistance } from "@/utils/distance";

import { Hero } from "@/components/Hero";
import { AboutSection } from "@/components/AboutSection";
import { SystemStatus } from "@/components/SystemStatus";

import { isRecent } from "@/utils/date";

export default function Home() {
  // Application State
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [isStale, setIsStale] = useState(false);
  
  // UI State
  const [selectedHospitalId, setSelectedHospitalId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("split");
  const [showHero, setShowHero] = useState(true);

  // Search state - lifted to pass to Header
  const [searchQuery, setSearchQuery] = useState("");
  
  // Geolocation state
  const [userLocation, setUserLocation] = useState<{lat: number, lon: number} | null>(null);
  const [sortByDistance, setSortByDistance] = useState(true); // Always default to distance if available
  const [showLiveOnly, setShowLiveOnly] = useState(false);
  const [locationRequested, setLocationRequested] = useState(false);

  // Handle explore click
  const handleExplore = () => {
    setShowHero(false);
  };
  
  // Request geolocation - called on page load
  // IP-based geolocation fallback (uses server-side proxy to avoid CORS)
  const fetchIPLocation = useCallback(async () => {
    try {
      const res = await fetch("/api/geolocation");
      const data = await res.json();
      
      if (data.success && data.location) {
        setUserLocation({
          lat: data.location.lat,
          lon: data.location.lon,
        });
        // sortByDistance is already true
        console.log("Using IP-based location:", data.location.city, data.location.region);
      }
    } catch (err) {
      console.warn("IP geolocation failed:", err);
      // Just use default Canada center, no location available
    }
  }, []);

  // Request geolocation - called on page load
  const requestLocation = useCallback(() => {
    if (locationRequested) return;
    setLocationRequested(true);
    
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
          // sortByDistance is already true
        },
        (error) => {
          console.warn("Geolocation denied or failed, falling back to IP location:", error.message);
          // Fallback to IP-based geolocation
          fetchIPLocation();
        },
        {
          enableHighAccuracy: false,
          timeout: 5000,
          maximumAge: 300000, // Cache for 5 minutes
        }
      );
    } else {
      // Browser doesn't support geolocation, use IP fallback
      fetchIPLocation();
    }
  }, [locationRequested, fetchIPLocation]);
  
  // Request location on mount
  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  // Fetch data
  useEffect(() => {
    async function fetchHospitals() {
      try {
        const res = await fetch("/api/hospitals?province=ON");
        const data = await res.json();
        
        if (data.success) {
          setHospitals(data.data);
          
          // Calculate freshness
          if (data.data.length > 0) {
             const updates = data.data
               .map((h: Hospital) => h.last_updated ? new Date(h.last_updated).getTime() : 0)
               .filter((t: number) => t > 0);
             
             if (updates.length > 0) {
               const maxTime = Math.max(...updates);
               setLastUpdate(new Date(maxTime).toISOString());
               
               const fourHoursAgo = Date.now() - (4 * 60 * 60 * 1000);
               setIsStale(maxTime < fourHoursAgo);
             }
          }
        } else {
          setError(data.message || "Failed to load data");
        }
      } catch (err) {
        console.error("Fetch error:", err);
        setError("Failed to load hospitals. Please try again later.");
      } finally {
        setLoading(false);
      }
    }
    
    fetchHospitals();
  }, []);

  // Filter and sort hospitals
  const filteredAndSortedHospitals = [...hospitals]
    .filter((hospital) => {
      // 1. Live Only Filter
      if (showLiveOnly && !isRecent(hospital.last_updated)) {
        return false;
      }

      // 2. Search Filter
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        hospital.name.toLowerCase().includes(query) ||
        hospital.city.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      // Always sort by distance if location is available
      if (userLocation) {
        const distA = calculateDistance(userLocation.lat, userLocation.lon, a.latitude, a.longitude);
        const distB = calculateDistance(userLocation.lat, userLocation.lon, b.latitude, b.longitude);
        return distA - distB;
      }
      // Fallback to alphabetical if no location
      return a.name.localeCompare(b.name);
    });

  // Count live hospitals
  const liveCount = hospitals.filter(h => isRecent(h.last_updated)).length;

  return (
    <main className="flex flex-col h-screen overflow-hidden bg-muted/20">
      <Header 
        viewMode={viewMode} 
        onViewModeChange={setViewMode}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        hospitalCount={hospitals.length}
        liveCount={liveCount}
        showStats={!showHero}
      />
      
      <div className={clsx(
        "flex-1 w-full flex flex-col relative",
        showHero ? "overflow-y-auto" : "overflow-hidden"
      )}>
        {/* Hero Section */}
        {showHero && (
          <div className="flex-shrink-0 animate-in fade-in slide-in-from-top-10 duration-500">
             {loading ? <HeroSkeleton /> : <Hero hospitals={hospitals} onExplore={handleExplore} userLocation={userLocation} />}
             {!loading && <AboutSection />}
          </div>
        )}

        {/* Main Split View Content - Responsive with max-width */}
        <div className={clsx(
          "flex-1 min-h-0 p-4 sm:p-6 lg:p-8",
          showHero && "h-[65vh] min-h-[65vh]" // Fixed height when scrolling to constrain map/list
        )}>
          <div className="h-full max-w-screen-2xl mx-auto">
            {/* Desktop: Side by side | Mobile: Show one view at a time */}
            <div className="h-full flex gap-4 sm:gap-6 lg:gap-8">
              {/* List View - Hidden on mobile in split mode */}
              {(viewMode === "list" || (viewMode === "split")) && (
                <div className={`${
                  viewMode === "split" 
                    ? "hidden lg:block lg:w-[35%]" // Hidden on mobile, 35% on desktop
                    : "w-full"
                } h-full`}>
                  <div className="h-full bg-card rounded-xl border border-border/50 shadow-sm overflow-hidden">
                    {error ? (
                      <div className="flex items-center justify-center h-full text-red-500">
                        {error}
                      </div>
                    ) : (
                      <HospitalList
                        hospitals={filteredAndSortedHospitals}
                        selectedId={selectedHospitalId}
                        onSelect={setSelectedHospitalId}
                        loading={loading}
                        searchQuery={searchQuery}
                        onSearchChange={setSearchQuery}
                        userLocation={userLocation}
                        onRequestLocation={requestLocation}
                        showLiveOnly={showLiveOnly}
                        onToggleLiveOnly={setShowLiveOnly}
                      />
                    )}
                  </div>
                </div>
              )}

              {/* Map View - Full width on mobile in split mode */}
              {(viewMode === "map" || viewMode === "split") && (
                <div className={`${
                  viewMode === "split" 
                    ? "w-full lg:w-[65%]" // Full on mobile, 65% on desktop
                    : "w-full"
                } h-full`}>
                  <div className="h-full bg-card rounded-xl border border-border/50 shadow-sm overflow-hidden">
                    <Map
                      hospitals={filteredAndSortedHospitals}
                      selectedId={selectedHospitalId}
                      onSelect={setSelectedHospitalId}
                      lastUpdate={lastUpdate}
                      isStale={isStale}
                      loading={loading}
                      error={error}
                      userLocation={userLocation}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer with System Status */}
      {!showHero && (
        <footer className="border-t border-border/50 bg-card/30 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-sm text-muted-foreground">
                <span>WaitTime Canada</span>
                <span className="mx-2">•</span>
                <a href="/methods" className="hover:text-foreground transition-colors">
                  Methodology
                </a>
              </div>
              <SystemStatus />
            </div>
          </div>
        </footer>
      )}
    </main>
  );
}
