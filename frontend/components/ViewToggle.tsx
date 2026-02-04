import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export type ViewMode = "list" | "map" | "split";

interface ViewToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
  className?: string;
}

export function ViewToggle({ mode, onChange, className }: ViewToggleProps) {
  return (
    <div
      className={twMerge(
        "flex p-1 bg-muted rounded-lg border border-border",
        className
      )}
    >
      <button
        onClick={() => onChange("list")}
        className={clsx(
          "flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-all",
          mode === "list"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground hover:bg-background/50"
        )}
      >
        List
      </button>
      <button
        onClick={() => onChange("map")}
        className={clsx(
          "flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-all",
          mode === "map"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground hover:bg-background/50"
        )}
      >
        Map
      </button>
      <button
        onClick={() => onChange("split")}
        className={clsx(
          "hidden md:block flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-all",
          mode === "split"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground hover:bg-background/50"
        )}
      >
        Split
      </button>
    </div>
  );
}
