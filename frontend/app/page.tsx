"use client";

import { useEffect, useState } from "react";
import Map from "@/components/Map";
import { HospitalList } from "@/components/HospitalList";
import { ViewToggle, ViewMode } from "@/components/ViewToggle";
import { Header } from "@/components/Header";
import type { Hospital } from "@/app/api/hospitals/route";

import { HeroSkeleton } from "@/components/skeletons/HeroSkeleton";
import { calculateDistance } from "@/utils/distance";

// ... imports

export default function Home() {
  // ... state
  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  
  // Geolocation state
  const [userLocation, setUserLocation] = useState<{lat: number, lon: number} | null>(null);
  const [sortByDistance, setSortByDistance] = useState(false);

  // Handle explore click
  const handleExplore = () => {
    setShowHero(false);
  };

  // Request location
  const requestLocation = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
          setSortByDistance(true);
        },
        (error) => {
          console.error("Error getting location:", error);
          // Could set an error state here specifically for location
        }
      );
    }
  };

  // Filter and sort hospitals
  const filteredAndSortedHospitals = [...hospitals]
    .filter((hospital) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        hospital.name.toLowerCase().includes(query) ||
        hospital.city.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      if (sortByDistance && userLocation) {
        // Sort by distance
        const distA = calculateDistance(userLocation.lat, userLocation.lon, a.lat, a.lon);
        const distB = calculateDistance(userLocation.lat, userLocation.lon, b.lat, b.lon);
        return distA - distB;
      }
      return 0; // Maintain original order (or default sort)
    });

  return (
    <main className="flex flex-col h-screen overflow-hidden">
      <Header viewMode={viewMode} onViewModeChange={setViewMode} />
      
      <div className="flex-1 w-full flex flex-col relative overflow-hidden">
        {/* Hero Section - Scrollable/Dismissible */}
        {showHero && (
          <div className="flex-shrink-0 animate-in fade-in slide-in-from-top-10 duration-500">
             {loading ? <HeroSkeleton /> : <Hero hospitals={hospitals} onExplore={handleExplore} />}
          </div>
        )}

        {/* Main Split View Content - Fills remaining space */}
        <div className="flex-1 min-h-0 flex relative overflow-hidden">
          {/* List View */}
          {(viewMode === "list" || viewMode === "split") && (
            <div className={`${viewMode === "split" ? "w-1/2 border-r border-border" : "w-full"} h-full`}>
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
                  sortByDistance={sortByDistance}
                  onSortChange={setSortByDistance}
                  onRequestLocation={requestLocation}
                />
              )}
            </div>
          )}

          {/* Map View */}
          {(viewMode === "map" || viewMode === "split") && (
            <div className={`${viewMode === "split" ? "w-1/2" : "w-full"} h-full`}>
              <Map
                hospitals={filteredAndSortedHospitals}
                selectedId={selectedHospitalId}
                onSelect={setSelectedHospitalId}
                lastUpdate={lastUpdate}
                isStale={isStale}
                loading={loading}
                error={error}
              />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

