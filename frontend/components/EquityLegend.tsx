import {
  EQUITY_QUINTILE_COLORS,
  type EquityLayerMetadata,
  type IncomeQuintile,
} from "@/utils/equity";

const quintileRows: Array<{ quintile: IncomeQuintile; label: string }> = [
  { quintile: 1, label: "Lowest 20%" },
  { quintile: 2, label: "20-40%" },
  { quintile: 3, label: "40-60%" },
  { quintile: 4, label: "60-80%" },
  { quintile: 5, label: "Highest 20%" },
];

interface EquityLegendProps {
  metadata?: EquityLayerMetadata;
}

export function EquityLegend({ metadata }: EquityLegendProps) {
  return (
    <div className="max-w-[240px] rounded-xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur-sm">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Income Quintile
      </h4>
      <div className="space-y-1.5">
        {quintileRows.map((row) => (
          <div key={row.quintile} className="flex items-center gap-2">
            <span
              className="h-3 w-4 rounded-sm border border-white/60 shadow-sm"
              style={{ backgroundColor: EQUITY_QUINTILE_COLORS[row.quintile] }}
            />
            <span className="text-xs text-slate-700">{row.label}</span>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[10px] leading-tight text-slate-500">
        {metadata?.attribution ??
          "Data attribution pending source integration."}
      </p>
      {metadata?.is_placeholder && (
        <p className="mt-1 text-[10px] font-medium text-amber-700">
          Placeholder layer (scaffold for integration)
        </p>
      )}
    </div>
  );
}
