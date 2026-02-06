# Equity Layer Implementation Guide

**Status:** Ready for implementation (research complete, blockers identified)
**Estimated Effort:** 8-10 hours
**Prerequisite:** Manual data download from Statistics Canada

---

## Overview

The equity layer visualizes socioeconomic disparities in emergency department access by overlaying census tract income data on the hospital map. This demonstrates the "Health Advocate" narrative and makes geographic health inequities visible.

**User Story:** _"As a health policy researcher, I want to see which emergency departments serve low-income census tracts, so I can identify access equity gaps."_

---

## Architecture

### Data Flow

```
Statistics Canada Census Data
  → GeoPandas Processing Script
    → Simplified GeoJSON (income quintiles)
      → Mapbox GL JS Fill Layer
        → Toggle control + Legend
```

### Tech Stack

- **Data Processing:** Python + GeoPandas + Pandas
- **Storage:** GeoJSON (or Mapbox Tileset if >2MB)
- **Frontend:** Mapbox GL JS + React
- **Data Source:** Statistics Canada Census 2021

---

## Phase 1: Data Acquisition (Manual, 1-2 hours)

### Step 1.1: Download Census Boundaries

**Source:** Statistics Canada Boundary Files
**URL:** https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm

**Download:**
1. Navigate to "2021 Census - Boundary files"
2. Select geographic level: **Census Tracts (CT)**
3. Select province: **Ontario** (35)
4. File format: **Shapefile (.shp)**
5. Coordinate system: **WGS84 (EPSG:4326)** (web mercator compatible)

**Expected Files:**
```
lct_000b21a_e.shp      # Geometry
lct_000b21a_e.shx      # Shape index
lct_000b21a_e.dbf      # Attributes
lct_000b21a_e.prj      # Projection
```

**Save to:** `/backend/data/census/boundaries/ontario/`

### Step 1.2: Download Income Data

**Source:** Statistics Canada Census Profile
**URL:** https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm

**Process:**
1. Select geography type: **Census tracts**
2. Select province: **Ontario**
3. Search for profile: **Income statistics**
4. Download CSV for:
   - **Median household income** (after tax)
   - **Median individual income** (after tax)
   - **Low income measure (LIM) percentage**

**Key Field:** `Median total income of household in 2020 ($)`

**Expected File:** `income_by_census_tract_ontario_2021.csv`

**Save to:** `/backend/data/census/income/ontario/`

### Step 1.3: Verify Data Integrity

```bash
cd backend/data/census

# Check shapefile integrity
ogrinfo boundaries/ontario/lct_000b21a_e.shp -al -so

# Check CSV structure
head -20 income/ontario/income_by_census_tract_ontario_2021.csv
```

**Expected Shapefile Attributes:**
- `CTUID` (Census Tract Unique Identifier)
- `CTNAME` (Census Tract Name)
- `PRUID` (Province ID: 35 for Ontario)

**Expected CSV Columns:**
- `GEO_UID` or `Census tract ID`
- Median income column (varies by download format)

---

## Phase 2: Data Processing (Python, 2-3 hours)

### Step 2.1: Install Dependencies

```bash
cd backend
source .venv/bin/activate

# Install geospatial libraries
pip install geopandas pandas pyproj shapely fiona
```

### Step 2.2: Create Processing Script

**File:** `/backend/scripts/prepare_equity_layer.py`

```python
"""Prepare census income equity layer for mapping.

Processes Statistics Canada Census 2021 data:
- Census tract boundaries (shapefile)
- Median household income (CSV)
- Output: Simplified GeoJSON with income quintiles

Usage:
    python scripts/prepare_equity_layer.py --province ON
"""

import argparse
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths
DATA_DIR = Path(__file__).parent.parent / "data" / "census"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "frontend" / "public" / "data"


def load_boundaries(province: str) -> gpd.GeoDataFrame:
    """Load census tract boundaries shapefile."""
    shp_path = DATA_DIR / "boundaries" / province.lower() / "lct_000b21a_e.shp"

    logger.info(f"Loading boundaries from {shp_path}")
    gdf = gpd.read_file(shp_path)

    # Ensure WGS84 projection (required for web maps)
    if gdf.crs.to_string() != "EPSG:4326":
        logger.info(f"Reprojecting from {gdf.crs} to EPSG:4326")
        gdf = gdf.to_crs("EPSG:4326")

    logger.info(f"Loaded {len(gdf)} census tracts")
    return gdf


def load_income_data(province: str) -> pd.DataFrame:
    """Load median income CSV."""
    csv_path = DATA_DIR / "income" / province.lower() / f"income_by_census_tract_{province.lower()}_2021.csv"

    logger.info(f"Loading income data from {csv_path}")
    df = pd.read_csv(csv_path)

    # Standardize column names (adjust based on actual CSV structure)
    # Example: rename GEO_UID to CTUID, income column to median_income
    if "GEO_UID" in df.columns:
        df = df.rename(columns={"GEO_UID": "CTUID"})

    # Find median income column (StatsCan format varies)
    income_col = [c for c in df.columns if "Median total income" in c][0]
    df = df.rename(columns={income_col: "median_income"})

    # Keep only necessary columns
    df = df[["CTUID", "median_income"]]

    # Clean data: remove non-numeric incomes
    df["median_income"] = pd.to_numeric(df["median_income"], errors="coerce")
    df = df.dropna(subset=["median_income"])

    logger.info(f"Loaded income data for {len(df)} census tracts")
    return df


def merge_and_process(boundaries: gpd.GeoDataFrame, income: pd.DataFrame) -> gpd.GeoDataFrame:
    """Merge boundaries with income and calculate quintiles."""
    logger.info("Merging boundaries with income data")

    # Merge on census tract ID
    merged = boundaries.merge(income, on="CTUID", how="left")

    # Drop tracts without income data
    merged = merged.dropna(subset=["median_income"])

    logger.info(f"Merged data: {len(merged)} census tracts with income data")

    # Calculate income quintiles (5 equal-sized groups)
    merged["income_quintile"] = pd.qcut(
        merged["median_income"],
        q=5,
        labels=[1, 2, 3, 4, 5],
        duplicates="drop"  # Handle ties
    )

    # Add descriptive labels
    quintile_labels = {
        1: "Lowest Income (Bottom 20%)",
        2: "Low Income (20-40%)",
        3: "Middle Income (40-60%)",
        4: "High Income (60-80%)",
        5: "Highest Income (Top 20%)",
    }
    merged["income_label"] = merged["income_quintile"].map(quintile_labels)

    # Simplify geometry to reduce file size
    # Tolerance: 0.001 degrees ≈ 100m (acceptable for web display)
    logger.info("Simplifying geometries")
    merged["geometry"] = merged["geometry"].simplify(tolerance=0.001, preserve_topology=True)

    # Keep only necessary columns for frontend
    merged = merged[["CTUID", "CTNAME", "median_income", "income_quintile", "income_label", "geometry"]]

    return merged


def export_geojson(gdf: gpd.GeoDataFrame, province: str, output_dir: Path) -> None:
    """Export to GeoJSON with size validation."""
    output_path = output_dir / f"{province.lower()}-equity-layer.geojson"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Exporting to {output_path}")
    gdf.to_file(output_path, driver="GeoJSON")

    # Check file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"File size: {file_size_mb:.2f} MB")

    if file_size_mb > 2.0:
        logger.warning("⚠️  File size exceeds 2MB. Consider using Mapbox Tilesets or further simplification.")
        logger.warning("Simplification options:")
        logger.warning("  1. Increase tolerance to 0.002 or 0.005")
        logger.warning("  2. Filter to only census tracts near hospitals")
        logger.warning("  3. Upload to Mapbox as tileset")
    else:
        logger.info("✅ File size acceptable for direct GeoJSON loading")


def main():
    parser = argparse.ArgumentParser(description="Prepare equity layer from census data")
    parser.add_argument("--province", default="ON", help="Province code (ON, QC, BC)")
    args = parser.parse_args()

    province = args.province.upper()

    # Load data
    boundaries = load_boundaries(province)
    income = load_income_data(province)

    # Process
    equity_layer = merge_and_process(boundaries, income)

    # Export
    export_geojson(equity_layer, province, OUTPUT_DIR)

    # Summary statistics
    logger.info("\n=== Summary ===")
    logger.info(f"Census tracts: {len(equity_layer)}")
    logger.info(f"Median income range: ${equity_layer['median_income'].min():,.0f} - ${equity_layer['median_income'].max():,.0f}")
    logger.info("\nIncome quintile distribution:")
    print(equity_layer.groupby("income_quintile")["CTUID"].count())


if __name__ == "__main__":
    main()
```

### Step 2.3: Run Processing Script

```bash
cd backend
python scripts/prepare_equity_layer.py --province ON
```

**Expected Output:**
```
INFO:__main__:Loading boundaries from data/census/boundaries/on/lct_000b21a_e.shp
INFO:__main__:Loaded 1395 census tracts
INFO:__main__:Loading income data from data/census/income/on/income_by_census_tract_on_2021.csv
INFO:__main__:Loaded income data for 1395 census tracts
INFO:__main__:Merging boundaries with income data
INFO:__main__:Merged data: 1395 census tracts with income data
INFO:__main__:Simplifying geometries
INFO:__main__:Exporting to ../frontend/public/data/on-equity-layer.geojson
INFO:__main__:File size: 1.87 MB
INFO:__main__:✅ File size acceptable for direct GeoJSON loading

=== Summary ===
Census tracts: 1395
Median income range: $24,000 - $185,600

Income quintile distribution:
income_quintile
1    279
2    279
3    279
4    279
5    279
```

### Step 2.4: Validate GeoJSON

```bash
# Install geojson validator
npm install -g @mapbox/geojsonhint

# Validate
geojsonhint frontend/public/data/on-equity-layer.geojson
```

**Expected:** No errors

---

## Phase 3: Frontend Integration (React + Mapbox, 3-4 hours)

### Step 3.1: Create Equity Layer Toggle

**File:** `/frontend/components/map/EquityLayerToggle.tsx`

```tsx
'use client';

import { Layers } from 'lucide-react';
import { clsx } from 'clsx';

interface EquityLayerToggleProps {
  enabled: boolean;
  onToggle: () => void;
}

export function EquityLayerToggle({ enabled, onToggle }: EquityLayerToggleProps) {
  return (
    <button
      onClick={onToggle}
      className={clsx(
        "absolute top-4 left-4 z-10",
        "px-3 py-2 rounded-lg shadow-md transition-all",
        "flex items-center gap-2 text-sm font-medium",
        enabled
          ? "bg-primary text-primary-foreground"
          : "bg-card border border-border text-foreground hover:bg-muted"
      )}
      title={enabled ? "Hide income overlay" : "Show income overlay"}
      aria-label={enabled ? "Hide income overlay" : "Show income overlay"}
      aria-pressed={enabled}
    >
      <Layers className="w-4 h-4" />
      <span>Income Layer</span>
    </button>
  );
}
```

### Step 3.2: Create Equity Legend

**File:** `/frontend/components/map/EquityLegend.tsx`

```tsx
'use client';

interface EquityLegendProps {
  show: boolean;
}

// Color scale: ColorBrewer YlOrRd (colorblind-safe)
const INCOME_COLORS = {
  1: '#feedde', // Lowest income (lightest)
  2: '#fdd0a2',
  3: '#fdae6b',
  4: '#fd8d3c',
  5: '#e6550d', // Highest income (darkest)
};

const INCOME_LABELS = {
  1: "Lowest (Bottom 20%)",
  2: "Low (20-40%)",
  3: "Middle (40-60%)",
  4: "High (60-80%)",
  5: "Highest (Top 20%)",
};

export function EquityLegend({ show }: EquityLegendProps) {
  if (!show) return null;

  return (
    <div className="absolute bottom-24 left-4 z-10 bg-card border border-border rounded-lg p-4 shadow-lg max-w-xs">
      <h4 className="text-xs font-semibold mb-3 text-foreground">
        Median Household Income by Census Tract
      </h4>

      <div className="space-y-2">
        {Object.entries(INCOME_COLORS).map(([quintile, color]) => (
          <div key={quintile} className="flex items-center gap-2">
            <div
              className="w-6 h-4 rounded border border-border"
              style={{ backgroundColor: color }}
              aria-hidden="true"
            />
            <span className="text-xs text-muted-foreground">
              {INCOME_LABELS[parseInt(quintile) as keyof typeof INCOME_LABELS]}
            </span>
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground mt-3 pt-3 border-t border-border">
        Data: Statistics Canada Census 2021
      </p>
    </div>
  );
}
```

### Step 3.3: Update Map Component

**File:** `/frontend/components/Map.tsx`

Add imports:
```tsx
import { useState } from 'react';
import { EquityLayerToggle } from './map/EquityLayerToggle';
import { EquityLegend } from './map/EquityLegend';
```

Add state:
```tsx
const [showEquityLayer, setShowEquityLayer] = useState(false);
```

Add layer effect:
```tsx
// Equity layer effect
useEffect(() => {
  if (!map) return;

  if (showEquityLayer) {
    // Add source
    if (!map.getSource('equity')) {
      map.addSource('equity', {
        type: 'geojson',
        data: '/data/on-equity-layer.geojson',
      });
    }

    // Add fill layer
    if (!map.getLayer('equity-fill')) {
      map.addLayer(
        {
          id: 'equity-fill',
          type: 'fill',
          source: 'equity',
          paint: {
            'fill-color': [
              'match',
              ['get', 'income_quintile'],
              1, '#feedde',
              2, '#fdd0a2',
              3, '#fdae6b',
              4, '#fd8d3c',
              5, '#e6550d',
              '#ccc', // Default
            ],
            'fill-opacity': 0.5,
          },
        },
        // Insert below hospital markers
        'hospital-markers-layer'
      );
    }

    // Add border layer for clarity
    if (!map.getLayer('equity-outline')) {
      map.addLayer({
        id: 'equity-outline',
        type: 'line',
        source: 'equity',
        paint: {
          'line-color': '#999',
          'line-width': 0.5,
          'line-opacity': 0.3,
        },
      });
    }
  } else {
    // Remove layers
    if (map.getLayer('equity-outline')) map.removeLayer('equity-outline');
    if (map.getLayer('equity-fill')) map.removeLayer('equity-fill');
    // Keep source for performance (toggle may happen frequently)
  }
}, [map, showEquityLayer]);
```

Add UI components:
```tsx
return (
  <div className="relative w-full h-full">
    <Map ref={mapRef} ... />

    {/* Add toggle and legend */}
    <EquityLayerToggle
      enabled={showEquityLayer}
      onToggle={() => setShowEquityLayer(!showEquityLayer)}
    />
    <EquityLegend show={showEquityLayer} />
  </div>
);
```

---

## Phase 4: Testing (1 hour)

### Unit Tests

**File:** `/frontend/tests/components/map/EquityLayerToggle.test.tsx`

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EquityLayerToggle } from '@/components/map/EquityLayerToggle';

describe('EquityLayerToggle', () => {
  it('renders with enabled state', () => {
    const onToggle = vi.fn();
    render(<EquityLayerToggle enabled={true} onToggle={onToggle} />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('Income Layer')).toBeInTheDocument();
  });

  it('calls onToggle when clicked', () => {
    const onToggle = vi.fn();
    render(<EquityLayerToggle enabled={false} onToggle={onToggle} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('shows correct label based on state', () => {
    const { rerender } = render(
      <EquityLayerToggle enabled={false} onToggle={() => {}} />
    );
    expect(screen.getByTitle('Show income overlay')).toBeInTheDocument();

    rerender(<EquityLayerToggle enabled={true} onToggle={() => {}} />);
    expect(screen.getByTitle('Hide income overlay')).toBeInTheDocument();
  });
});
```

### Integration Tests

```tsx
describe('Map with Equity Layer', () => {
  it('toggles equity layer on and off', async () => {
    render(<Map hospitals={[]} ... />);

    const toggle = screen.getByRole('button', { name: /show income overlay/i });
    fireEvent.click(toggle);

    // Layer should be added to map
    await waitFor(() => {
      expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true');
    });

    // Legend should appear
    expect(screen.getByText(/Median Household Income/i)).toBeInTheDocument();
  });

  it('displays legend when layer is active', () => {
    render(<Map hospitals={[]} showEquityLayer={true} />);
    expect(screen.getByText('Statistics Canada Census 2021')).toBeInTheDocument();
  });
});
```

### Manual Testing Checklist

- [ ] Toggle button appears in top-left corner
- [ ] Clicking toggle shows/hides census tract overlay
- [ ] Legend appears when layer is active
- [ ] Legend shows 5 income quintiles with colors
- [ ] Colors are distinct and accessible
- [ ] Layer renders below hospital markers
- [ ] Map performance is acceptable (no lag on pan/zoom)
- [ ] Mobile: Toggle and legend are usable on small screens
- [ ] Mobile: Layer doesn't cause performance issues

### Performance Testing

```bash
# Check GeoJSON file size
ls -lh frontend/public/data/on-equity-layer.geojson

# Should be < 2MB
# If larger, re-run prepare_equity_layer.py with higher tolerance
```

### Accessibility Testing

- [ ] Color contrast meets WCAG AA standards
- [ ] Colorblind-safe palette (use ColorBrewer YlOrRd)
- [ ] Keyboard navigation works (toggle button focusable)
- [ ] Screen reader announces layer state

---

## Troubleshooting

### Issue: GeoJSON file too large (>2MB)

**Solution 1:** Increase simplification tolerance
```python
merged["geometry"] = merged["geometry"].simplify(tolerance=0.005, preserve_topology=True)
```

**Solution 2:** Filter to hospital proximity
```python
# Only include census tracts within 50km of any hospital
hospitals_gdf = get_hospitals_as_geodataframe()
buffer = hospitals_gdf.unary_union.buffer(0.5)  # ~50km buffer
merged = merged[merged.intersects(buffer)]
```

**Solution 3:** Upload to Mapbox Tilesets
```bash
# Install Mapbox CLI
npm install -g @mapbox/mapbox-cli

# Upload tileset
mapbox upload username.equity-layer on-equity-layer.geojson
```

Update Map.tsx:
```tsx
map.addSource('equity', {
  type: 'vector',
  url: 'mapbox://username.equity-layer',
});
```

### Issue: Slow map performance

**Diagnosis:**
```javascript
// Add to Map.tsx for debugging
map.on('render', () => {
  console.log('Frame render time:', map.painter.renderTime);
});
```

**Solution:** Reduce layer complexity
- Increase geometry simplification tolerance
- Use vector tiles instead of GeoJSON
- Limit visible zoom levels:
```tsx
map.addLayer({
  ...
  minzoom: 8,  // Only show when zoomed in
  maxzoom: 16,
});
```

### Issue: Missing income data for some census tracts

**Check:** CSV and shapefile have matching CTUID values
```python
# In prepare_equity_layer.py
print(f"Boundaries: {len(boundaries)} tracts")
print(f"Income data: {len(income)} tracts")
print(f"Merged: {len(merged)} tracts")
print(f"Missing: {len(boundaries) - len(merged)} tracts")
```

**Solution:** Use left join and handle nulls
```python
merged = boundaries.merge(income, on="CTUID", how="left")
merged["income_quintile"] = merged["income_quintile"].fillna(0)  # 0 = No Data
```

Add "No Data" category to legend.

---

## Documentation Requirements

### Update /methods Page

Add section:

```markdown
## Equity Layer Methodology

**Data Source:** Statistics Canada Census 2021

**Geographic Unit:** Census Tracts (CTs)

**Income Metric:** Median total household income after tax (2020)

**Classification:** Income quintiles (5 equal groups based on distribution)

**Projection:** WGS84 (EPSG:4326)

**Simplification:** Tolerance 0.001 degrees (~100m) to reduce file size

**Attribution:** All census data © Statistics Canada, licensed under the Open Government Licence - Canada

**Limitations:**
- Census data from 2021 (may not reflect current income distribution)
- Census tracts are administrative boundaries, not perfect representations of neighborhoods
- Income quintiles are relative (province-specific), not absolute poverty measures
```

### Create Data Attribution File

**File:** `/frontend/public/data/README.md`

```markdown
# Data Attribution

## ontario-equity-layer.geojson

**Source:** Statistics Canada, Census of Population, 2021
**URL:** https://www12.statcan.gc.ca/census-recensement/2021/

**Data Elements:**
- Census tract boundaries (© Statistics Canada)
- Median total income of household in 2020 ($)

**License:** Open Government Licence - Canada
**URL:** https://open.canada.ca/en/open-government-licence-canada

**Modifications:**
- Geometries simplified to tolerance 0.001 degrees
- Income data classified into quintiles
- Projected to WGS84 (EPSG:4326)

**Processing Date:** [Auto-generated by script]

**Recommended Citation:**
"Emergency department equity analysis based on Statistics Canada Census 2021 data. © Statistics Canada."
```

---

## Deployment

### Production Checklist

- [ ] GeoJSON files committed to `/frontend/public/data/`
- [ ] File size verified (<2MB or tileset uploaded)
- [ ] Attribution displayed in legend
- [ ] /methods page updated
- [ ] Data README created
- [ ] Tests passing
- [ ] Performance validated on mobile
- [ ] Accessibility tested
- [ ] Analytics tracking added (equity layer usage)

### Monitoring

Track equity layer usage:
```tsx
// In Map.tsx
useEffect(() => {
  if (showEquityLayer) {
    // Log to analytics
    trackEvent('equity_layer_enabled', { province: 'ON' });
  }
}, [showEquityLayer]);
```

Monitor performance:
- Page load time with/without layer
- Map FPS during pan/zoom with layer active
- User engagement (% of users who enable layer)

---

## Future Enhancements

### Multi-Province Support

1. Download census data for QC, BC
2. Process into separate GeoJSON files
3. Dynamically load based on map viewport or selected province

```tsx
const equityLayerUrl = `/data/${province.toLowerCase()}-equity-layer.geojson`;
```

### Additional Socioeconomic Indicators

- **Low Income Measure (LIM):** % of population below poverty line
- **Visible Minority Population:** % by census tract
- **Recent Immigrants:** % arrived in last 5 years
- **Primary Language:** Non-official language speakers

**UI:** Dropdown to select indicator
```tsx
<select onChange={e => setEquityMetric(e.target.value)}>
  <option value="income">Median Income</option>
  <option value="lim">Low Income (%)</option>
  <option value="minority">Visible Minority (%)</option>
</select>
```

### Interactive Tooltips

Show census tract details on hover:
```tsx
map.on('mousemove', 'equity-fill', (e) => {
  const { CTNAME, median_income, income_label } = e.features[0].properties;

  popup.setHTML(`
    <strong>${CTNAME}</strong><br/>
    Median Income: $${median_income.toLocaleString()}<br/>
    Quintile: ${income_label}
  `).setLngLat(e.lngLat).addTo(map);
});
```

### Equity Analysis Reports

Generate insights:
```tsx
function analyzeEquity(hospitals, equityLayer) {
  // Calculate: What % of ERs are in low-income areas?
  const lowIncomeERs = hospitals.filter(h =>
    equityLayer.find(ct => ct.contains(h.location) && ct.income_quintile <= 2)
  );

  return {
    totalERs: hospitals.length,
    lowIncomeERs: lowIncomeERs.length,
    pct: (lowIncomeERs.length / hospitals.length * 100).toFixed(1),
  };
}
```

Display in dashboard:
```tsx
<p>
  {analysis.lowIncomeERs} of {analysis.totalERs} ERs ({analysis.pct}%)
  serve census tracts in the lowest 40% income bracket.
</p>
```

---

## Conclusion

The equity layer is **ready for implementation** once census data is downloaded. All technical specifications, code examples, and troubleshooting guidance are documented above.

**Next Steps:**
1. Allocate 1-2 hours for manual data download
2. Run processing script (2-3 hours)
3. Implement frontend components (3-4 hours)
4. Test and deploy (1 hour)

**Total Estimated Time:** 8-10 hours

**Value Delivered:**
- Visual equity analysis for health policy research
- Demonstrates "Health Advocate" competency
- Unique feature among ER wait time platforms
- Foundation for future socioeconomic analyses

---

**Questions or Issues?**
- Consult GeoPandas documentation: https://geopandas.org/
- Mapbox GL JS examples: https://docs.mapbox.com/mapbox-gl-js/example/
- Statistics Canada data guide: https://www12.statcan.gc.ca/census-recensement/2021/ref/dict/index-eng.cfm
