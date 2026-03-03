import { clsx } from "clsx";
import { useTranslations } from "next-intl";

export type ViewMode = "list" | "map" | "split";

interface ViewToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
  className?: string;
}

export function ViewToggle({ mode, onChange, className }: ViewToggleProps) {
  const t = useTranslations("ViewToggle");

  return (
    <div
      className={clsx(
        "flex p-1 bg-muted/50 rounded-xl border border-border/50",
        className,
      )}
    >
      <button
        onClick={() => onChange("list")}
        aria-label="List view"
        className={clsx(
          "flex-1 px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 flex items-center justify-center gap-1.5",
          mode === "list"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground hover:bg-background/50",
        )}
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 10h16M4 14h16M4 18h16"
          />
        </svg>
        <span className="hidden sm:inline">{t("list")}</span>
      </button>
      <button
        onClick={() => onChange("map")}
        aria-label="Map view"
        className={clsx(
          "flex-1 px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 flex items-center justify-center gap-1.5",
          mode === "map"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground hover:bg-background/50",
        )}
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
          />
        </svg>
        <span className="hidden sm:inline">{t("map")}</span>
      </button>
      <button
        onClick={() => onChange("split")}
        aria-label="Split view"
        className={clsx(
          "hidden md:flex flex-1 px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 items-center justify-center gap-1.5",
          mode === "split"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground hover:bg-background/50",
        )}
      >
        {t("split")}
      </button>
    </div>
  );
}
