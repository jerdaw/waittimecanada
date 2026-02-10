import { clsx } from "clsx";

interface ProvinceFilterProps {
  selectedProvince: string;
  onProvinceChange: (province: string) => void;
  className?: string;
}

const PROVINCES = [
  { code: "ON", name: "Ontario" },
  { code: "QC", name: "Quebec" },
  { code: "BC", name: "British Columbia" },
] as const;

export function ProvinceFilter({
  selectedProvince,
  onProvinceChange,
  className,
}: ProvinceFilterProps) {
  return (
    <select
      value={selectedProvince}
      onChange={(e) => onProvinceChange(e.target.value)}
      className={clsx(
        "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
        "bg-background border-border text-foreground hover:bg-muted/50",
        "cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/20",
        className,
      )}
      aria-label="Filter by province"
    >
      {PROVINCES.map((p) => (
        <option key={p.code} value={p.code}>
          {p.name}
        </option>
      ))}
    </select>
  );
}
