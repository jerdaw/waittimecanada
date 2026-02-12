import { clsx } from "clsx";

interface OccupancyBadgeProps {
  percentage: number;
  size?: "sm" | "md";
  className?: string;
}

/**
 * Display stretcher occupancy percentage with color-coded indicator.
 *
 * Color coding:
 * - Green (<90%): Below capacity, good access
 * - Yellow (90-110%): Near or at capacity
 * - Red (>110%): Overcrowded, potential delays
 *
 * Quebec-specific metric based on current patients / stretcher capacity.
 */
export function OccupancyBadge({
  percentage,
  size = "sm",
  className,
}: OccupancyBadgeProps) {
  // Determine color based on occupancy level
  const getOccupancyColor = (pct: number) => {
    if (pct < 90) return "success"; // Below capacity
    if (pct <= 110) return "warning"; // Near/at capacity
    return "danger"; // Overcrowded
  };

  const color = getOccupancyColor(percentage);
  const isSmall = size === "sm";

  return (
    <div
      className={clsx(
        "inline-flex items-center gap-1 rounded font-medium tabular-nums",
        isSmall ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs",
        color === "success" &&
          "bg-success/10 text-success border border-success/20",
        color === "warning" &&
          "bg-warning/10 text-warning border border-warning/20",
        color === "danger" &&
          "bg-danger/10 text-danger border border-danger/20",
        className,
      )}
      title={
        percentage > 100
          ? `Stretcher occupancy: ${percentage.toFixed(0)}% (Overcrowded)`
          : `Stretcher occupancy: ${percentage.toFixed(0)}%`
      }
    >
      <span
        className={clsx(
          "rounded-full shrink-0",
          isSmall ? "w-1 h-1" : "w-1.5 h-1.5",
          color === "success" && "bg-success",
          color === "warning" && "bg-warning",
          color === "danger" && "bg-danger animate-pulse",
        )}
      />
      <span>{Math.round(percentage)}%</span>
    </div>
  );
}
