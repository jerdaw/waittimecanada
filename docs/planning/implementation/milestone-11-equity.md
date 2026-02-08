# Milestone 11: Access & Equity Features

> **Priority:** HIGH - Strongest "Health Advocate" features for admissions
> **Estimated Effort:** 5-6 days
> **Admissions Appeal:** Health Advocate (access barriers), Scholar (equity analysis)

---

## Implementation Status (Updated 2026-02-08)

- Access Burden Estimator: implemented and test-covered
- Equity layer foundation scaffold: implemented
  - `/api/equity-layer` placeholder GeoJSON flow (Ontario)
  - Map toggle + legend integration in `Map.tsx`
  - Clear placeholder attribution/labeling to avoid overclaiming
- Tract-linked equity summary: implemented (placeholder-aware)
  - `/api/analytics/equity-summary` linkage metrics (low-income tract proximity + wait-time gap)
  - `AccessInsightsSummary` now surfaces equity snapshot alongside personal access estimates
- Remaining for full M11 completion:
  - Replace placeholder data with StatsCan census tract income layer
  - Recompute linkage summary with real provincial tract datasets

---

## Overview

These features demonstrate awareness that healthcare access is about more than wait times. The Access Burden Estimator highlights financial barriers, while the Equity Layer visualizes socioeconomic disparities in ER access.

**Narrative for Applications:**
> "I built an 'Access Burden Estimator' to highlight the hidden financial barriers to emergency care—travel costs, parking fees, and time off work. This isn't about discouraging people from seeking care; it's about making visible the barriers that policymakers often ignore."

---

## Phase 1: Access Burden Estimator (Days 1-3)

### 1.1 Design Requirements

**Purpose:** Show users the estimated logistical cost of reaching a specific ER.

**Formula:**
```
Access Burden = (Distance × Gas Cost per km) + Parking Estimate + Time Cost
```

**Components:**
- **Distance:** Already calculated (user location → hospital)
- **Gas Cost:** Provincial average gas price × estimated fuel consumption
- **Parking:** Hospital-specific or default estimate
- **Time Cost:** Optional - travel time × minimum wage (very sensitive, may omit)

**Critical Disclaimer:**
> "This is a logistical planning tool only. **Never delay emergency care for cost.** If you're experiencing a medical emergency, call 911 immediately."

### 1.2 Data Sources

**Gas Prices:**
- Source: Natural Resources Canada or GasBuddy API
- Fallback: Static provincial averages (update monthly)
- Fuel consumption: 10L/100km average vehicle

**Provincial Gas Price Defaults (CAD/L):**
```json
{
  "ON": 1.55,
  "QC": 1.60,
  "AB": 1.45,
  "BC": 1.75,
  "MB": 1.50,
  "SK": 1.48
}
```

**Parking Estimates:**
- Urban hospital default: $15-25
- Suburban hospital default: $10-15
- Rural hospital default: $0-5
- Override per hospital if data available

### 1.3 Component Implementation

**File:** `frontend/components/AccessBurdenEstimator.tsx`

```tsx
'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, Car, ParkingCircle, Clock } from 'lucide-react';

interface AccessBurdenEstimatorProps {
  distanceKm: number;
  province: string;
  hospitalType?: 'urban' | 'suburban' | 'rural';
}

// Provincial gas prices (CAD/L) - update periodically
const GAS_PRICES: Record<string, number> = {
  ON: 1.55, QC: 1.60, AB: 1.45, BC: 1.75, MB: 1.50, SK: 1.48,
  NS: 1.58, NB: 1.55, PE: 1.52, NL: 1.65,
};

// Parking estimates by hospital type
const PARKING_ESTIMATES = {
  urban: { min: 15, max: 25 },
  suburban: { min: 10, max: 15 },
  rural: { min: 0, max: 5 },
};

// Average fuel consumption (L/100km)
const FUEL_CONSUMPTION = 10;

export function AccessBurdenEstimator({
  distanceKm,
  province,
  hospitalType = 'urban',
}: AccessBurdenEstimatorProps) {
  const [expanded, setExpanded] = useState(false);

  const gasPrice = GAS_PRICES[province] || 1.55;
  const fuelCost = (distanceKm * 2 * FUEL_CONSUMPTION / 100) * gasPrice; // Round trip
  const parking = PARKING_ESTIMATES[hospitalType];
  const parkingMid = (parking.min + parking.max) / 2;
  const totalMin = fuelCost + parking.min;
  const totalMax = fuelCost + parking.max;

  return (
    <div className="border border-amber-200 dark:border-amber-800 rounded-lg bg-amber-50 dark:bg-amber-950/30">
      {/* Disclaimer Banner */}
      <div className="px-4 py-2 bg-amber-100 dark:bg-amber-900/50 border-b border-amber-200 dark:border-amber-800 rounded-t-lg">
        <div className="flex items-start gap-2 text-amber-800 dark:text-amber-200">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <p className="text-xs">
            <strong>Planning tool only.</strong> Never delay emergency care for cost.
            Call 911 for emergencies.
          </p>
        </div>
      </div>

      {/* Collapsible Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-amber-100/50 dark:hover:bg-amber-900/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Car className="w-4 h-4 text-amber-600" />
          <span className="font-medium text-slate-900 dark:text-white">
            Access Burden Estimate
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-amber-700 dark:text-amber-300">
            ${totalMin.toFixed(0)} - ${totalMax.toFixed(0)}
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded Details */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 animate-in fade-in slide-in-from-top-2">
          {/* Fuel Cost */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <Car className="w-4 h-4" />
              <span>Fuel ({(distanceKm * 2).toFixed(0)} km round trip)</span>
            </div>
            <span className="font-medium text-slate-900 dark:text-white">
              ${fuelCost.toFixed(2)}
            </span>
          </div>

          {/* Parking */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <ParkingCircle className="w-4 h-4" />
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
            Based on {FUEL_CONSUMPTION}L/100km fuel consumption at ${gasPrice.toFixed(2)}/L ({province}).
            Actual costs vary by vehicle and current fuel prices.
          </p>
        </div>
      )}
    </div>
  );
}
```

### 1.4 Integration Points

**In Hospital Card (expanded view):**
```tsx
{userLocation && (
  <AccessBurdenEstimator
    distanceKm={calculateDistance(userLocation, hospital)}
    province={hospital.province}
    hospitalType={hospital.hospital_type || 'urban'}
  />
)}
```

**In Map Popup:**
```tsx
{userLocation && (
  <AccessBurdenEstimator
    distanceKm={distanceToHospital}
    province={selectedHospital.province}
  />
)}
```

### 1.5 Tests

**File:** `frontend/tests/components/AccessBurdenEstimator.test.tsx`

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { AccessBurdenEstimator } from '@/components/AccessBurdenEstimator';

describe('AccessBurdenEstimator', () => {
  it('renders with collapsed view showing estimate range', () => {
    render(<AccessBurdenEstimator distanceKm={20} province="ON" />);
    expect(screen.getByText(/Access Burden Estimate/)).toBeInTheDocument();
    expect(screen.getByText(/\$\d+ - \$\d+/)).toBeInTheDocument();
  });

  it('shows disclaimer about not delaying care', () => {
    render(<AccessBurdenEstimator distanceKm={20} province="ON" />);
    expect(screen.getByText(/Never delay emergency care/)).toBeInTheDocument();
  });

  it('expands to show detailed breakdown', () => {
    render(<AccessBurdenEstimator distanceKm={20} province="ON" />);
    fireEvent.click(screen.getByText(/Access Burden Estimate/));
    expect(screen.getByText(/round trip/)).toBeInTheDocument();
    expect(screen.getByText(/Parking/)).toBeInTheDocument();
  });

  it('calculates fuel cost correctly', () => {
    // 20km × 2 (round trip) × 10L/100km × $1.55/L = $6.20
    render(<AccessBurdenEstimator distanceKm={20} province="ON" />);
    fireEvent.click(screen.getByText(/Access Burden Estimate/));
    expect(screen.getByText('$6.20')).toBeInTheDocument();
  });

  it('uses correct gas price for province', () => {
    render(<AccessBurdenEstimator distanceKm={20} province="BC" />);
    fireEvent.click(screen.getByText(/Access Burden Estimate/));
    // BC gas: $1.75/L → 20×2×10/100×1.75 = $7.00
    expect(screen.getByText('$7.00')).toBeInTheDocument();
  });
});
```

### 1.6 ADR

**File:** `docs/adr/0005-access-burden-estimator.md`

```markdown
# ADR 0005: Access Burden Estimator Design

## Status
Accepted

## Context
Healthcare access involves more than wait times. Travel costs, parking fees, and time
off work create barriers that disproportionately affect lower-income patients.

## Decision
Implement a collapsible "Access Burden Estimator" that shows:
- Fuel cost based on distance and provincial gas prices
- Parking estimate based on hospital type
- Total estimated cost range

## Safeguards
1. **Prominent disclaimer** - "Never delay emergency care for cost"
2. **Collapsed by default** - Users must actively choose to see it
3. **Presented as estimate** - Range, not precise figure
4. **No time cost** - Avoided calculating "lost wages" as too sensitive

## Consequences
- **Positive:** Makes financial barriers visible to users and policymakers
- **Positive:** Demonstrates "Health Advocate" competency for applications
- **Risk:** Could be misinterpreted as advice to avoid care
- **Mitigation:** Strong disclaimers and default collapsed state
```

---

## Phase 2: Equity Layer / Socioeconomic Overlay (Days 4-5)

### 2.1 Data Source Research

**Statistics Canada Options:**

1. **Census Tract Income Data**
   - Source: 2021 Census
   - URL: https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm
   - Format: CSV or GeoJSON
   - Variables: Median household income, low-income measure (LIM)

2. **Canadian Index of Multiple Deprivation (CIMD)**
   - Source: Statistics Canada
   - Dimensions: Residential instability, economic dependency, ethno-cultural composition, situational vulnerability
   - Better for holistic "deprivation" measure

3. **Postal Code Level Data**
   - Less granular but easier to match to user location
   - PCCF+ (Postal Code Conversion File Plus)

**Recommended Approach:** Use census tract median income quintiles for Ontario first, expand to other provinces later.

### 2.2 Data Preparation

**Steps:**
1. Download Ontario census tract GeoJSON from StatsCan
2. Join with income data (median household income)
3. Calculate quintiles (1 = lowest 20%, 5 = highest 20%)
4. Simplify geometry for web performance
5. Convert to Mapbox tileset or serve as GeoJSON

**File:** `backend/scripts/prepare_equity_layer.py`

```python
"""Prepare census tract equity layer for Mapbox."""
import geopandas as gpd
import pandas as pd

def prepare_equity_layer(
    census_tracts_path: str,
    income_data_path: str,
    output_path: str
):
    """
    Join census tract boundaries with income data and calculate quintiles.

    Args:
        census_tracts_path: Path to census tract GeoJSON
        income_data_path: Path to income CSV from StatsCan
        output_path: Path for output GeoJSON
    """
    # Load census tracts
    tracts = gpd.read_file(census_tracts_path)

    # Load income data
    income = pd.read_csv(income_data_path)

    # Join on census tract ID
    merged = tracts.merge(
        income[['CTUID', 'median_household_income']],
        left_on='CTUID',
        right_on='CTUID',
        how='left'
    )

    # Calculate income quintiles
    merged['income_quintile'] = pd.qcut(
        merged['median_household_income'],
        q=5,
        labels=[1, 2, 3, 4, 5]
    )

    # Simplify geometry for web (tolerance in degrees, ~100m)
    merged['geometry'] = merged['geometry'].simplify(0.001)

    # Save
    merged.to_file(output_path, driver='GeoJSON')
    print(f"Saved {len(merged)} census tracts to {output_path}")

if __name__ == '__main__':
    prepare_equity_layer(
        census_tracts_path='data/boundaries/ontario-census-tracts.geojson',
        income_data_path='data/census/ontario-income-2021.csv',
        output_path='data/layers/ontario-equity-layer.geojson'
    )
```

### 2.3 Mapbox Integration

**Option A: GeoJSON Layer (simpler, for small datasets)**

```tsx
// In Map.tsx
const [showEquityLayer, setShowEquityLayer] = useState(false);

useEffect(() => {
  if (!map || !showEquityLayer) return;

  // Add equity layer source
  map.addSource('equity', {
    type: 'geojson',
    data: '/api/equity-layer', // Serve GeoJSON from API
  });

  // Add fill layer with quintile-based coloring
  map.addLayer({
    id: 'equity-fill',
    type: 'fill',
    source: 'equity',
    paint: {
      'fill-color': [
        'match',
        ['get', 'income_quintile'],
        1, '#fee5d9', // Lowest income - lightest red
        2, '#fcae91',
        3, '#fb6a4a',
        4, '#de2d26',
        5, '#a50f15', // Highest income - darkest red
        '#ccc', // Default
      ],
      'fill-opacity': 0.4,
    },
  });

  return () => {
    map.removeLayer('equity-fill');
    map.removeSource('equity');
  };
}, [map, showEquityLayer]);
```

**Option B: Mapbox Tileset (for large datasets)**

Upload GeoJSON to Mapbox Studio → create tileset → reference tileset ID in code.

### 2.4 Toggle Component

**File:** `frontend/components/EquityLayerToggle.tsx`

```tsx
'use client';

import { Layers } from 'lucide-react';

interface EquityLayerToggleProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
}

export function EquityLayerToggle({ enabled, onChange }: EquityLayerToggleProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onChange(!enabled)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
          enabled
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
            : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200'
        }`}
      >
        <Layers className="w-4 h-4" />
        Income Overlay
      </button>
    </div>
  );
}
```

### 2.5 Legend Component

**File:** `frontend/components/EquityLegend.tsx`

```tsx
export function EquityLegend() {
  const quintiles = [
    { label: 'Lowest 20%', color: '#fee5d9' },
    { label: '20-40%', color: '#fcae91' },
    { label: '40-60%', color: '#fb6a4a' },
    { label: '60-80%', color: '#de2d26' },
    { label: 'Highest 20%', color: '#a50f15' },
  ];

  return (
    <div className="absolute bottom-4 left-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-3 z-10">
      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
        Median Household Income
      </h4>
      <div className="space-y-1">
        {quintiles.map((q) => (
          <div key={q.label} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded"
              style={{ backgroundColor: q.color }}
            />
            <span className="text-xs text-slate-600 dark:text-slate-400">
              {q.label}
            </span>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-slate-400 mt-2">
        Source: Statistics Canada 2021 Census
      </p>
    </div>
  );
}
```

### 2.6 Equity Insights Summary

**On /methods or /insights page:**

```tsx
export function EquityInsights({ hospitals, equityData }) {
  // Calculate: hospitals within 30km of low-income areas
  const lowIncomeAreas = equityData.filter(t => t.income_quintile <= 2);

  const hospitalsNearLowIncome = hospitals.filter(h => {
    return lowIncomeAreas.some(area =>
      isWithinDistance(h, area.centroid, 30) // 30km
    );
  });

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-6">
      <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
        Access Equity Insights
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <p className="text-3xl font-bold text-blue-600">
            {hospitalsNearLowIncome.length}
          </p>
          <p className="text-sm text-slate-500">
            ERs within 30km of low-income areas
          </p>
        </div>

        <div className="text-center p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <p className="text-3xl font-bold text-amber-600">
            {/* Calculate average wait in low-income areas */}
          </p>
          <p className="text-sm text-slate-500">
            Avg wait time in underserved areas
          </p>
        </div>
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-400 mt-4">
        Income data from Statistics Canada 2021 Census. "Low-income" defined as
        bottom 40% of median household income by census tract.
      </p>
    </div>
  );
}
```

---

## Phase 3: Documentation (Day 6)

### 3.1 ADR for Equity Layer

**File:** `docs/adr/0011-equity-layer-scaffold.md`

```markdown
# ADR 0011: Equity Layer Scaffold-First Delivery

## Status
Accepted

## Context
Healthcare access disparities correlate with socioeconomic status. Visualizing
this relationship helps users and policymakers understand access barriers.

## Decision
Implement an optional map overlay showing census tract median household income
by quintile, with legend and data attribution.

## Data Source
Statistics Canada 2021 Census, census tract level, median household income.

## Privacy Considerations
- Data is aggregated at census tract level (no individual identification)
- Source is public Statistics Canada data
- No personal data collected from users

## Limitations
- Income is a proxy for access barriers, not a direct measure
- Census data is 5 years old (2021)
- Does not account for transit access, insurance status, etc.

## Consequences
- **Positive:** Makes socioeconomic disparities visible
- **Positive:** Supports policy discussions about ER placement
- **Risk:** Could be seen as stigmatizing low-income areas
- **Mitigation:** Frame as "access insight" not "risk assessment"
```

---

## Verification Checklist

### Access Burden Estimator
- [x] Component renders with collapsed view
- [x] Disclaimer is visible and prominent
- [x] Expands to show fuel + parking breakdown
- [x] Uses correct provincial gas prices
- [x] Calculates round-trip distance
- [x] Tests pass
- [x] ADR documented

### Equity Layer
- [ ] Census tract data downloaded and processed
- [x] GeoJSON layer loads in Mapbox (placeholder scaffold payload)
- [x] Toggle shows/hides layer
- [x] Legend explains quintiles
- [x] Data attribution visible
- [x] Tract-linked equity summary shown with wait-time linkage metrics
- [x] ADR documented (scaffold-first approach)

---

## Success Criteria

1. **Access Burden Estimator** visible in hospital cards with clear disclaimer
2. **Equity Layer** toggleable on map with legend
3. **Both features** documented with ADRs
4. **Narrative ready** for applications explaining "Health Advocate" angle

---

## Time Estimate

| Task | Hours |
|------|-------|
| Access Burden Estimator component | 3-4 |
| Estimator integration + tests | 2 |
| Estimator ADR | 0.5 |
| Census data download + processing | 3-4 |
| Mapbox layer integration | 2-3 |
| Toggle + legend components | 1-2 |
| Equity insights summary | 2 |
| Equity ADR | 0.5 |
| **Total** | **14-18 hours** |
