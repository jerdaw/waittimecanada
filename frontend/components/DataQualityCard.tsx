"use client";

interface SourceQuality {
  source_id: string;
  source_name: string;
  province: string;
  last_24h_success_rate: number;
  last_7d_success_rate: number;
  hospitals_reporting: number;
  total_hospitals: number;
  last_heartbeat_age_minutes: number | null;
  scraper_status: string;
}

interface DataQualityCardProps {
  source: SourceQuality;
}

function getRateColor(rate: number): string {
  if (rate >= 0.95) return "text-green-600 dark:text-green-400";
  if (rate >= 0.8) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

function getRateBg(rate: number): string {
  if (rate >= 0.95) return "bg-green-100 dark:bg-green-900/30";
  if (rate >= 0.8) return "bg-amber-100 dark:bg-amber-900/30";
  return "bg-red-100 dark:bg-red-900/30";
}

function getStatusDot(status: string): string {
  if (status === "healthy") return "bg-green-500";
  if (status === "error") return "bg-red-500";
  if (status === "stale") return "bg-amber-500";
  return "bg-gray-400";
}

function formatAge(minutes: number | null): string {
  if (minutes === null) return "Never";
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function DataQualityCard({ source }: DataQualityCardProps) {
  const rate24h = source.last_24h_success_rate;
  const rate7d = source.last_7d_success_rate;

  return (
    <div className="bg-card rounded-lg border border-border/50 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${getStatusDot(source.scraper_status)}`} />
          <h3 className="font-semibold text-sm">{source.source_name}</h3>
          <span className="text-xs text-muted-foreground">({source.province})</span>
        </div>
        <span className="text-xs text-muted-foreground">
          {formatAge(source.last_heartbeat_age_minutes)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {/* 24h Success Rate */}
        <div className={`rounded-md p-2 ${getRateBg(rate24h)}`}>
          <div className="text-xs text-muted-foreground mb-0.5">24h Rate</div>
          <div className={`text-lg font-bold tabular-nums ${getRateColor(rate24h)}`}>
            {(rate24h * 100).toFixed(1)}%
          </div>
        </div>

        {/* 7d Success Rate */}
        <div className={`rounded-md p-2 ${getRateBg(rate7d)}`}>
          <div className="text-xs text-muted-foreground mb-0.5">7d Rate</div>
          <div className={`text-lg font-bold tabular-nums ${getRateColor(rate7d)}`}>
            {(rate7d * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {source.hospitals_reporting}/{source.total_hospitals} hospitals reporting
        </span>
      </div>
    </div>
  );
}
