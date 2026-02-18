"use client";

import { Layers } from "lucide-react";

interface EquityLayerToggleProps {
  enabled: boolean;
  loading?: boolean;
  onChange: (enabled: boolean) => void;
  enabledLabel?: string;
  disabledLabel?: string;
  loadingLabel?: string;
  enableAriaLabel?: string;
  disableAriaLabel?: string;
}

export function EquityLayerToggle({
  enabled,
  loading = false,
  onChange,
  enabledLabel = "Income Overlay On",
  disabledLabel = "Income Overlay Off",
  loadingLabel = "Loading...",
  enableAriaLabel = "Enable income overlay",
  disableAriaLabel = "Disable income overlay",
}: EquityLayerToggleProps) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      aria-pressed={enabled}
      aria-label={enabled ? disableAriaLabel : enableAriaLabel}
      className={[
        "inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium shadow-sm backdrop-blur-sm transition-colors",
        enabled
          ? "border-blue-200 bg-blue-50/95 text-blue-700 hover:bg-blue-100"
          : "border-slate-200 bg-white/95 text-slate-700 hover:bg-white",
      ].join(" ")}
    >
      <Layers className="h-4 w-4" />
      <span>{enabled ? enabledLabel : disabledLabel}</span>
      {loading && (
        <span className="text-xs text-slate-500">{loadingLabel}</span>
      )}
    </button>
  );
}
