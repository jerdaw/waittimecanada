"use client";

import { useTranslations } from "next-intl";

export interface RegionOption {
  region_id: string;
  region_name: string;
  hospital_count: number;
  reporting_count: number;
}

interface RegionSelectorProps {
  regions: RegionOption[];
  selectedRegionId: string | null;
  onRegionChange: (regionId: string | null) => void;
  disabled?: boolean;
}

export function RegionSelector({
  regions,
  selectedRegionId,
  onRegionChange,
  disabled = false,
}: RegionSelectorProps) {
  const t = useTranslations('RegionSelector');
  const value = selectedRegionId ?? "all";

  return (
    <label className="inline-flex items-center gap-2 text-xs text-muted-foreground">
      <span className="font-medium">{t('label')}</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => {
          const next = event.target.value;
          onRegionChange(next === "all" ? null : next);
        }}
        className="rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
      >
        <option value="all">{t('allRegions')}</option>
        {regions.map((region) => (
          <option key={region.region_id} value={region.region_id}>
            {region.region_name} ({region.reporting_count}/
            {region.hospital_count})
          </option>
        ))}
      </select>
    </label>
  );
}
