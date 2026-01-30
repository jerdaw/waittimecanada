"use client";

import { useEffect, useState } from "react";
import MapGL, { Marker, Popup } from "react-map-gl";
import type { Hospital } from "@/app/api/hospitals/route";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

// Color-code by wait time
function getMarkerColor(waitTimeMinutes: number | undefined): string {
  if (!waitTimeMinutes) return "#gray";
  if (waitTimeMinutes < 60) return "#22c55e"; // green
  if (waitTimeMinutes < 120) return "#eab308"; // yellow
  return "#ef4444"; // red
}

export default function Map() {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [selectedHospital, setSelectedHospital] = useState<Hospital | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHospitals() {
      try {
        const response = await fetch("/api/hospitals");
        const result = await response.json();

        if (!result.success) {
          throw new Error(result.message || "Failed to fetch hospitals");
        }

        setHospitals(result.data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
        setLoading(false);
      }
    }

    fetchHospitals();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-lg">Loading hospitals...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-red-600">Error: {error}</p>
          <p className="mt-2 text-sm text-gray-600">
            Check console for details
          </p>
        </div>
      </div>
    );
  }

  if (!MAPBOX_TOKEN) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="max-w-md text-center">
          <p className="text-lg text-red-600">Mapbox token not configured</p>
          <p className="mt-2 text-sm text-gray-600">
            Copy <code className="bg-gray-100 px-1">.env.local.example</code> to{" "}
            <code className="bg-gray-100 px-1">.env.local</code> and add your
            Mapbox token
          </p>
        </div>
      </div>
    );
  }

  // Center map on Canada
  const initialViewState = {
    latitude: 56.1304,
    longitude: -106.3468,
    zoom: 4,
  };

  return (
    <div className="relative h-screen w-full">
      <MapGL
        {...initialViewState}
        mapboxAccessToken={MAPBOX_TOKEN}
        mapStyle="mapbox://styles/mapbox/streets-v12"
        style={{ width: "100%", height: "100%" }}
      >
        {hospitals.map((hospital) => (
          <Marker
            key={hospital.id}
            latitude={hospital.latitude}
            longitude={hospital.longitude}
            anchor="bottom"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setSelectedHospital(hospital);
            }}
          >
            <div
              className="h-6 w-6 cursor-pointer rounded-full border-2 border-white shadow-lg transition-transform hover:scale-110"
              style={{
                backgroundColor: getMarkerColor(hospital.current_wait_time),
              }}
              title={hospital.name}
            />
          </Marker>
        ))}

        {selectedHospital && (
          <Popup
            latitude={selectedHospital.latitude}
            longitude={selectedHospital.longitude}
            onClose={() => setSelectedHospital(null)}
            closeOnClick={false}
            anchor="top"
          >
            <div className="p-2">
              <h3 className="font-bold">{selectedHospital.name}</h3>
              <p className="text-sm text-gray-600">
                {selectedHospital.city}, {selectedHospital.province}
              </p>
              {selectedHospital.current_wait_time ? (
                <div className="mt-2">
                  <p className="text-lg font-semibold">
                    {Math.round(selectedHospital.current_wait_time)} min
                  </p>
                  <p className="text-xs text-gray-500">
                    Last updated:{" "}
                    {selectedHospital.last_updated
                      ? new Date(selectedHospital.last_updated).toLocaleString()
                      : "Unknown"}
                  </p>
                </div>
              ) : (
                <p className="mt-2 text-sm text-gray-500">No data available</p>
              )}
            </div>
          </Popup>
        )}
      </MapGL>

      {/* Legend */}
      <div className="absolute bottom-8 left-8 rounded-lg bg-white p-4 shadow-lg">
        <h4 className="mb-2 text-sm font-bold">Wait Time</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 rounded-full bg-[#22c55e]" />
            <span>&lt; 60 min</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 rounded-full bg-[#eab308]" />
            <span>60-120 min</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 rounded-full bg-[#ef4444]" />
            <span>&gt; 120 min</span>
          </div>
        </div>
      </div>

      {/* Hospital count */}
      <div className="absolute right-8 top-8 rounded-lg bg-white p-3 shadow-lg">
        <p className="text-sm">
          <span className="font-bold">{hospitals.length}</span> hospitals
          tracked
        </p>
      </div>
    </div>
  );
}
