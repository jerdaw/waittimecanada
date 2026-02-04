import { ViewMode, ViewToggle } from "./ViewToggle";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

export function Header({ viewMode, onViewModeChange }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2">
          <div className="bg-primary/10 p-1.5 rounded-lg">
            <svg
              className="w-5 h-5 text-primary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
          </div>
          <span className="font-bold text-lg hidden sm:inline-block">
            WaitTime Canada
          </span>
          <span className="font-bold text-lg sm:hidden">WTC</span>
        </div>

        <div className="flex items-center gap-4">
          <ViewToggle mode={viewMode} onChange={onViewModeChange} />
          <div className="w-px h-6 bg-border mx-1" />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
