"use client";

import { useEffect, useState } from "react";

interface UnverifiedHospital {
  id: string;
  name: string;
  province: string;
  city: string;
  latitude: number;
  longitude: number;
  source_id: string;
  created_at: string;
  is_visible: boolean;
  is_verified: boolean;
}

interface ApiResponse {
  success: boolean;
  count?: number;
  data?: UnverifiedHospital[];
  error?: string;
  message?: string;
}

export default function VerifyHospitalsPage() {
  const [hospitals, setHospitals] = useState<UnverifiedHospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  // Fetch unverified hospitals on mount
  useEffect(() => {
    fetchUnverifiedHospitals();
  }, []);

  const fetchUnverifiedHospitals = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("/api/admin/hospitals/unverified");
      const data: ApiResponse = await response.json();

      if (data.success && data.data) {
        setHospitals(data.data);
      } else {
        setError(data.error || "Failed to fetch hospitals");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (
    hospitalId: string,
    makeVisible: boolean = true
  ) => {
    if (processingIds.has(hospitalId)) return;

    setProcessingIds((prev) => new Set(prev).add(hospitalId));

    try {
      const response = await fetch(
        `/api/admin/hospitals/${hospitalId}/verify`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ makeVisible }),
        }
      );

      const data: ApiResponse = await response.json();

      if (data.success) {
        // Remove from list
        setHospitals((prev) => prev.filter((h) => h.id !== hospitalId));
      } else {
        alert(`Failed to verify: ${data.error || "Unknown error"}`);
      }
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setProcessingIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(hospitalId);
        return newSet;
      });
    }
  };

  const handleReject = async (hospitalId: string) => {
    if (
      !confirm(
        "Are you sure you want to reject this hospital? This will permanently delete it from the database."
      )
    ) {
      return;
    }

    if (processingIds.has(hospitalId)) return;

    setProcessingIds((prev) => new Set(prev).add(hospitalId));

    try {
      const response = await fetch(
        `/api/admin/hospitals/${hospitalId}/verify`,
        {
          method: "DELETE",
        }
      );

      const data: ApiResponse = await response.json();

      if (data.success) {
        // Remove from list
        setHospitals((prev) => prev.filter((h) => h.id !== hospitalId));
      } else {
        alert(`Failed to reject: ${data.error || "Unknown error"}`);
      }
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setProcessingIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(hospitalId);
        return newSet;
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Hospital Verification Queue</h1>
          <p className="text-gray-600">Loading unverified hospitals...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Hospital Verification Queue</h1>
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            <strong>Error:</strong> {error}
          </div>
          <button
            onClick={fetchUnverifiedHospitals}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Hospital Verification Queue</h1>
            <p className="text-gray-600 mt-2">
              Review and approve hospitals discovered by scrapers
            </p>
          </div>
          <div className="text-sm text-gray-500">
            {hospitals.length} pending verification
          </div>
        </div>

        {hospitals.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h2 className="text-xl font-semibold mb-2">All Caught Up!</h2>
            <p className="text-gray-600">
              No hospitals pending verification at this time.
            </p>
            <button
              onClick={fetchUnverifiedHospitals}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {hospitals.map((hospital) => {
              const isProcessing = processingIds.has(hospital.id);

              return (
                <div
                  key={hospital.id}
                  className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold mb-2">
                        {hospital.name}
                      </h3>
                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                        <div>
                          <strong>Location:</strong> {hospital.city},{" "}
                          {hospital.province}
                        </div>
                        <div>
                          <strong>Coordinates:</strong> {hospital.latitude.toFixed(4)},{" "}
                          {hospital.longitude.toFixed(4)}
                        </div>
                        <div>
                          <strong>Source:</strong> {hospital.source_id}
                        </div>
                        <div>
                          <strong>Discovered:</strong>{" "}
                          {new Date(hospital.created_at).toLocaleDateString()}
                        </div>
                        <div>
                          <strong>Hospital ID:</strong>{" "}
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                            {hospital.id}
                          </code>
                        </div>
                      </div>
                    </div>

                    <div className="ml-6 flex flex-col gap-2">
                      <button
                        onClick={() => handleVerify(hospital.id, true)}
                        disabled={isProcessing}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {isProcessing ? "Processing..." : "✓ Approve & Publish"}
                      </button>
                      <button
                        onClick={() => handleVerify(hospital.id, false)}
                        disabled={isProcessing}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {isProcessing
                          ? "Processing..."
                          : "✓ Approve (Keep Hidden)"}
                      </button>
                      <button
                        onClick={() => handleReject(hospital.id)}
                        disabled={isProcessing}
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {isProcessing ? "Processing..." : "✗ Reject & Delete"}
                      </button>
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
