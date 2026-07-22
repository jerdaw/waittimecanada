"use client";

import { clsx } from "clsx";
import { useEffect, useState, useCallback, useMemo } from "react";
import Map from "@/components/Map";
import { HospitalList } from "@/components/HospitalList";
import { ViewToggle, ViewMode } from "@/components/ViewToggle";
import { Header } from "@/components/Header";
import type { Hospital } from "@/app/api/hospitals/route";

import { HeroSkeleton } from "@/components/skeletons/HeroSkeleton";
import { calculateDistance } from "@/utils/distance";

import { Hero } from "@/components/Hero";
import { AboutSection } from "@/components/AboutSection";
import { Testimonial } from "@/components/Testimonial";
import { Footer } from "@/components/Footer";
import { AccessInsightsSummary } from "@/components/insights/AccessInsightsSummary";
import {
  RegionDashboard,
  type RegionAnalyticsRow,
} from "@/components/RegionDashboard";
import type { RegionOption } from "@/components/RegionSelector";
import { getFeaturedTestimonial } from "@/content/stakeholderTestimonials";

import { isRecent } from "@/utils/date";
import { useTranslations } from "next-intl";
import type { PublicCoverage } from "@/types/coverage";
import { HEARTBEAT_STALE_THRESHOLD_MINUTES } from "@/utils/live-scraper-sources";

interface HomePageClientProps {
  initialHospitals: Hospital[];
  initialCoverage: PublicCoverage | null;
}

const HOSPITAL_REFRESH_INTERVAL_MS = 5 * 60 * 1000;

export function HomePageClient({
  initialHospitals,
  initialCoverage,
}: HomePageClientProps) {
  const t = useTranslations("HomePage");
  const REGION_PERIOD = "7d";
  const featuredTestimonial = getFeaturedTestimonial();

  // Application State
  const [hospitals, setHospitals] = useState<Hospital[]>(initialHospitals);
  const [coverage, setCoverage] = useState<PublicCoverage | null>(
    initialCoverage,
  );
  const [loading, setLoading] = useState(initialHospitals.length === 0);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [isStale, setIsStale] = useState(false);

  // UI State
  const [selectedHospitalId, setSelectedHospitalId] = useState<string | null>(
    null,
  );
  const [viewMode, setViewMode] = useState<ViewMode>("split");
  const [showHero, setShowHero] = useState(true);

  // Search state - lifted to pass to Header
  const [searchQuery, setSearchQuery] = useState("");

  // Province filter state
  const [selectedProvince, setSelectedProvince] = useState("ON");
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [regionRows, setRegionRows] = useState<RegionAnalyticsRow[]>([]);
  const [provinceRegionMean, setProvinceRegionMean] = useState<number | null>(
    null,
  );
  const [regionsLoading, setRegionsLoading] = useState(false);

  // Geolocation state
  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lon: number;
  } | null>(null);
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
          console.warn(
            "Geolocation denied or failed, falling back to IP location:",
            error.message,
          );
          // Fallback to IP-based geolocation
          fetchIPLocation();
        },
        {
          enableHighAccuracy: false,
          timeout: 5000,
          maximumAge: 300000, // Cache for 5 minutes
        },
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

  // Refresh the selected province on mount, province changes, every five minutes
  // while visible, and immediately when the tab becomes visible again.
  useEffect(() => {
    let cancelled = false;

    async function fetchHospitals() {
      if (hospitals.length === 0) setLoading(true);
      setError(null);

      try {
        const res = await fetch(`/api/hospitals?province=${selectedProvince}`);
        const data = await res.json();

        if (!cancelled && data.success) {
          setHospitals(data.data);
          setCoverage(data.coverage ?? null);

          // Calculate freshness
          if (data.data.length > 0) {
            const updates = data.data
              .map((h: Hospital) =>
                h.last_updated ? new Date(h.last_updated).getTime() : 0,
              )
              .filter((t: number) => t > 0);

            if (updates.length > 0) {
              const maxTime = Math.max(...updates);
              setLastUpdate(new Date(maxTime).toISOString());

              const staleBoundary =
                Date.now() - HEARTBEAT_STALE_THRESHOLD_MINUTES * 60 * 1000;
              setIsStale(maxTime < staleBoundary);
            }
          }
        } else if (!cancelled) {
          setError(data.message || t("error.loadFailed"));
        }
      } catch (err) {
        console.error("Fetch error:", err);
        if (!cancelled) setError(t("error.fetchFailed"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void fetchHospitals();

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void fetchHospitals();
      }
    };
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void fetchHospitals();
      }
    }, HOSPITAL_REFRESH_INTERVAL_MS);

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
    // hospitals.length is deliberately omitted so a successful refresh does not
    // recreate the polling interval.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProvince, t]);

  useEffect(() => {
    if (showHero) {
      setRegionsLoading(false);
      setSelectedRegionId(null);
      setRegionRows([]);
      setProvinceRegionMean(null);
      return;
    }

    let cancelled = false;

    async function fetchRegionAnalytics() {
      setRegionsLoading(true);
      setSelectedRegionId(null);

      try {
        const query = new URLSearchParams({
          province: selectedProvince,
          period: REGION_PERIOD,
        });
        const response = await fetch(
          `/api/analytics/regions?${query.toString()}`,
        );
        const payload = await response.json();

        if (!cancelled && payload.success && payload.data) {
          setRegionRows(payload.data.regions ?? []);
          setProvinceRegionMean(
            payload.data.province_mean === null
              ? null
              : Number(payload.data.province_mean),
          );
        } else if (!cancelled) {
          setRegionRows([]);
          setProvinceRegionMean(null);
        }
      } catch (err) {
        console.error("Failed to fetch region analytics:", err);
        if (!cancelled) {
          setRegionRows([]);
          setProvinceRegionMean(null);
        }
      } finally {
        if (!cancelled) {
          setRegionsLoading(false);
        }
      }
    }

    fetchRegionAnalytics();
    return () => {
      cancelled = true;
    };
  }, [selectedProvince, REGION_PERIOD, showHero]);

  const selectedRegionHospitalIds = useMemo(() => {
    if (!selectedRegionId) return null;
    const selectedRegion = regionRows.find(
      (region) => region.region_id === selectedRegionId,
    );
    if (!selectedRegion) return null;
    return new Set(selectedRegion.hospital_ids);
  }, [regionRows, selectedRegionId]);

  const regionOptions: RegionOption[] = useMemo(
    () =>
      regionRows.map((region) => ({
        region_id: region.region_id,
        region_name: region.region_name,
        hospital_count: region.hospital_count,
        reporting_count: region.reporting_count,
      })),
    [regionRows],
  );

  // Filter and sort hospitals
  const filteredAndSortedHospitals = [...hospitals]
    .filter((hospital) => {
      // 0. Region Filter
      if (
        selectedRegionHospitalIds &&
        !selectedRegionHospitalIds.has(hospital.id)
      ) {
        return false;
      }

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
        const distA = calculateDistance(
          userLocation.lat,
          userLocation.lon,
          a.latitude,
          a.longitude,
        );
        const distB = calculateDistance(
          userLocation.lat,
          userLocation.lon,
          b.latitude,
          b.longitude,
        );
        return distA - distB;
      }
      // Fallback to alphabetical if no location
      return a.name.localeCompare(b.name);
    });

  // Count live hospitals
  const liveCount = hospitals.filter((h) => isRecent(h.last_updated)).length;

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

      <div
        className={clsx("flex-1 w-full flex flex-col relative overflow-y-auto")}
      >
        {/* Hero Section */}
        {showHero && (
          <div className="flex-shrink-0 animate-in fade-in slide-in-from-top-10 duration-500">
            <Hero
              hospitals={hospitals}
              coverage={coverage}
              onExplore={handleExplore}
              userLocation={userLocation}
              loading={loading}
              selectedProvince={selectedProvince}
              onProvinceChange={setSelectedProvince}
              onSelectHospital={setSelectedHospitalId}
            />
            {featuredTestimonial && (
              <div className="px-6 pb-6 max-w-md mx-auto lg:mx-0 lg:ml-6">
                <Testimonial testimonial={featuredTestimonial} />
              </div>
            )}
          </div>
        )}

        {/* Access Insights Section - Only show when Hero is dismissed */}
        {!showHero && !loading && hospitals.length > 0 && (
          <div
            className={clsx(
              "flex-shrink-0 px-4 sm:px-6 lg:px-8 pt-6 animate-in fade-in duration-500",
              viewMode === "map" && "hidden lg:block",
            )}
          >
            <div className="max-w-screen-2xl mx-auto">
              <h2 className="text-lg font-semibold mb-4 text-foreground">
                {t("accessInsights")}
              </h2>
              <AccessInsightsSummary
                hospitals={hospitals}
                userLocation={userLocation}
                province={selectedProvince}
              />
              <div className="mt-4">
                <RegionDashboard
                  province={selectedProvince}
                  period={REGION_PERIOD}
                  regions={regionRows}
                  provinceMean={provinceRegionMean}
                  loading={regionsLoading}
                  selectedRegionId={selectedRegionId}
                  onSelectRegion={setSelectedRegionId}
                />
              </div>
            </div>
          </div>
        )}

        {/* Mobile hint: in split mode on mobile, the list is hidden — prompt users to switch */}
        {!showHero && viewMode === "split" && (
          <div className="lg:hidden flex-shrink-0 px-4 pb-2">
            <p
              className="text-xs text-center text-muted-foreground"
              dangerouslySetInnerHTML={{ __html: t.raw("mobileHint") }}
            />
          </div>
        )}

        {/* Main Split View Content - Responsive with max-width */}
        <div
          className={clsx(
            "flex-1 p-4 sm:p-6 lg:p-8",
            showHero ? "h-[45vh] min-h-[45vh]" : "h-full min-h-[650px]",
          )}
        >
          <div className="h-full max-w-screen-2xl mx-auto">
            {/* Desktop: Side by side | Mobile: Show one view at a time */}
            <div className="h-full flex gap-4 sm:gap-6 lg:gap-8">
              {/* List View - Hidden on mobile in split mode */}
              {(viewMode === "list" || viewMode === "split") && (
                <div
                  className={`${
                    viewMode === "split"
                      ? "hidden lg:block lg:w-[35%]" // Hidden on mobile, 35% on desktop
                      : "w-full"
                  } h-full`}
                >
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
                        selectedProvince={selectedProvince}
                        onProvinceChange={setSelectedProvince}
                        regionOptions={regionOptions}
                        selectedRegionId={selectedRegionId}
                        onRegionChange={setSelectedRegionId}
                        regionsLoading={regionsLoading}
                      />
                    )}
                  </div>
                </div>
              )}

              {/* Map View - Full width on mobile in split mode */}
              {(viewMode === "map" || viewMode === "split") && (
                <div
                  className={`${
                    viewMode === "split"
                      ? "w-full lg:w-[65%]" // Full on mobile, 65% on desktop
                      : "w-full"
                  } h-full`}
                >
                  <div className="h-full bg-card rounded-xl border border-border/50 shadow-sm overflow-hidden">
                    <Map
                      hospitals={filteredAndSortedHospitals}
                      province={selectedProvince}
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

      {/* About Section - only shown after hero dismiss */}
      {!showHero && (
        <div className="flex-shrink-0 animate-in fade-in duration-700">
          <AboutSection />
        </div>
      )}

      {/* Footer */}
      {!showHero && <Footer />}
    </main>
  );
}
