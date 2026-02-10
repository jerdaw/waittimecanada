"use client";

interface CoverageDay {
  date: string;
  scrape_count: number;
  success_rate: number;
}

interface CoverageHeatmapProps {
  timeline: CoverageDay[];
  hospitalId: string;
}

function getCellColor(rate: number): string {
  if (rate === 0) return "bg-gray-100 dark:bg-gray-800";
  if (rate < 0.5) return "bg-green-100 dark:bg-green-900/20";
  if (rate < 0.8) return "bg-green-300 dark:bg-green-800/40";
  if (rate < 0.95) return "bg-green-400 dark:bg-green-700/60";
  return "bg-green-600 dark:bg-green-600/80";
}

export function CoverageHeatmap({
  timeline,
  hospitalId,
}: CoverageHeatmapProps) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="text-sm text-muted-foreground text-center py-4">
        No coverage data available
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>Data Coverage (last {timeline.length} days)</span>
        <div className="flex items-center gap-1 ml-auto">
          <span>0%</span>
          <div className="flex gap-px">
            <div className="w-3 h-3 rounded-sm bg-gray-100 dark:bg-gray-800" />
            <div className="w-3 h-3 rounded-sm bg-green-100 dark:bg-green-900/20" />
            <div className="w-3 h-3 rounded-sm bg-green-300 dark:bg-green-800/40" />
            <div className="w-3 h-3 rounded-sm bg-green-400 dark:bg-green-700/60" />
            <div className="w-3 h-3 rounded-sm bg-green-600 dark:bg-green-600/80" />
          </div>
          <span>100%</span>
        </div>
      </div>
      <div
        className="flex gap-px flex-wrap"
        role="grid"
        aria-label="Data coverage heatmap"
      >
        {timeline.map((day) => (
          <div
            key={day.date}
            className={`w-4 h-4 rounded-sm ${getCellColor(day.success_rate)} cursor-default`}
            title={`${day.date}: ${day.scrape_count} scrapes (${(day.success_rate * 100).toFixed(0)}%)`}
            role="gridcell"
          />
        ))}
      </div>
    </div>
  );
}
