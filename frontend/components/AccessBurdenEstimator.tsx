"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Car,
  ParkingCircle,
} from "lucide-react";

interface AccessBurdenEstimatorProps {
  distanceKm: number;
  province: string;
  hospitalType?: "urban" | "suburban" | "rural";
}

// Provincial gas prices (CAD/L) - Updated periodically from Natural Resources Canada
const GAS_PRICES: Record<string, number> = {
  ON: 1.55,
  QC: 1.6,
  AB: 1.45,
  BC: 1.75,
  MB: 1.5,
  SK: 1.48,
  NS: 1.58,
  NB: 1.55,
  PE: 1.52,
  NL: 1.65,
  YT: 1.7,
  NT: 1.75,
  NU: 1.8,
};

// Parking estimates by hospital type (CAD)
const PARKING_ESTIMATES = {
  urban: { min: 15, max: 25 },
  suburban: { min: 10, max: 15 },
  rural: { min: 0, max: 5 },
};

// Average fuel consumption (L/100km) for typical passenger vehicle
const FUEL_CONSUMPTION = 10;

export function AccessBurdenEstimator({
  distanceKm,
  province,
  hospitalType = "urban",
}: AccessBurdenEstimatorProps) {
  const [expanded, setExpanded] = useState(false);

  // Calculate costs
  const gasPrice = GAS_PRICES[province] || 1.55; // Default to Ontario
  const roundTripKm = distanceKm * 2;
  const fuelCost = ((roundTripKm * FUEL_CONSUMPTION) / 100) * gasPrice;
  const parking = PARKING_ESTIMATES[hospitalType];
  const parkingMid = (parking.min + parking.max) / 2;
  const totalMin = fuelCost + parking.min;
  const totalMax = fuelCost + parking.max;

  return (
    <div className="border border-amber-200 dark:border-amber-800 rounded-lg bg-amber-50 dark:bg-amber-950/30 overflow-hidden">
      {/* Disclaimer Banner - Always Visible */}
      <div className="px-4 py-2 bg-amber-100 dark:bg-amber-900/50 border-b border-amber-200 dark:border-amber-800">
        <div className="flex items-start gap-2 text-amber-800 dark:text-amber-200">
          <AlertTriangle
            className="w-4 h-4 mt-0.5 flex-shrink-0"
            aria-hidden="true"
          />
          <p className="text-xs">
            <strong>Planning tool only.</strong> Never delay emergency care for
            cost. Call 911 for emergencies.
          </p>
        </div>
      </div>

      {/* Collapsible Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-amber-100/50 dark:hover:bg-amber-900/30 transition-colors"
        aria-expanded={expanded}
        aria-label={
          expanded
            ? "Collapse access burden details"
            : "Expand access burden details"
        }
      >
        <div className="flex items-center gap-2">
          <Car
            className="w-4 h-4 text-amber-600 dark:text-amber-400"
            aria-hidden="true"
          />
          <span className="font-medium text-slate-900 dark:text-white">
            Access Burden Estimate
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-amber-700 dark:text-amber-300">
            ${totalMin.toFixed(0)} - ${totalMax.toFixed(0)}
          </span>
          {expanded ? (
            <ChevronUp
              className="w-4 h-4 text-slate-400 flex-shrink-0"
              aria-hidden="true"
            />
          ) : (
            <ChevronDown
              className="w-4 h-4 text-slate-400 flex-shrink-0"
              aria-hidden="true"
            />
          )}
        </div>
      </button>

      {/* Expanded Details */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
          {/* Fuel Cost */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <Car className="w-4 h-4" aria-hidden="true" />
              <span>Fuel ({roundTripKm.toFixed(0)} km round trip)</span>
            </div>
            <span className="font-medium text-slate-900 dark:text-white">
              ${fuelCost.toFixed(2)}
            </span>
          </div>

          {/* Parking */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <ParkingCircle className="w-4 h-4" aria-hidden="true" />
              <span>Parking ({hospitalType} hospital)</span>
            </div>
            <span className="font-medium text-slate-900 dark:text-white">
              ${parking.min} - ${parking.max}
            </span>
          </div>

          {/* Divider */}
          <div className="border-t border-amber-200 dark:border-amber-800 pt-2">
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-700 dark:text-slate-300">
                Estimated Total
              </span>
              <span className="text-lg font-bold text-amber-700 dark:text-amber-300">
                ${totalMin.toFixed(0)} - ${totalMax.toFixed(0)}
              </span>
            </div>
          </div>

          {/* Methodology Note */}
          <p className="text-xs text-slate-500 dark:text-slate-400 pt-2">
            Based on {FUEL_CONSUMPTION}L/100km fuel consumption at $
            {gasPrice.toFixed(2)}/L ({province}). Actual costs vary by vehicle
            and current fuel prices. Parking estimates are typical for{" "}
            {hospitalType} hospitals in Canada.
          </p>

          {/* Additional Context */}
          <div className="pt-2 border-t border-amber-200 dark:border-amber-800">
            <p className="text-xs text-slate-600 dark:text-slate-400">
              <strong>Why show this?</strong> Financial barriers to healthcare
              access are often invisible. This estimate makes logistical costs
              explicit for patients and policymakers, but should never influence
              the decision to seek emergency care.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
