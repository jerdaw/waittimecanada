'use client';

import { Layers } from "lucide-react";

interface EquityLayerToggleProps {
  enabled: boolean;
  loading?: boolean;
  onChange: (enabled: boolean) => void;
}

export function EquityLayerToggle({ enabled, loading = false, onChange }: EquityLayerToggleProps) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      aria-pressed={enabled}
      aria-label={enabled ? "Disable income overlay" : "Enable income overlay"}
      className={[
        "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium shadow-sm backdrop-blur-sm transition-colors",
        enabled
          ? "border-blue-200 bg-blue-50/95 text-blue-700 hover:bg-blue-100"
          : "border-slate-200 bg-white/95 text-slate-700 hover:bg-white",
      ].join(" ")}
    >
      <Layers className="h-4 w-4" />
      <span>{enabled ? "Income Overlay On" : "Income Overlay Off"}</span>
      {loading && <span className="text-xs text-slate-500">Loading...</span>}
    </button>
  );
}
