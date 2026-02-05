import Link from "next/link";
import { ViewMode, ViewToggle } from "./ViewToggle";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  viewMode?: ViewMode;
  onViewModeChange?: (mode: ViewMode) => void;
  // New props for search and stats
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  hospitalCount?: number;
  liveCount?: number;
  showStats?: boolean;
}

export function Header({ 
  viewMode, 
  onViewModeChange,
  searchQuery = "",
  onSearchChange,
  hospitalCount,
  liveCount,
  showStats = false,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-border/40 bg-background/70 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60 shadow-sm transition-all">
      {/* Main Header Row */}
      <div className="container flex h-16 items-center justify-between px-4 sm:px-6 gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity group shrink-0">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary to-accent rounded-lg blur-sm opacity-50 group-hover:opacity-75 transition-opacity" />
            <div className="relative bg-gradient-to-br from-primary to-primary-hover p-1.5 rounded-lg shadow-md">
              <svg
                className="w-4 h-4 text-white"
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
          </div>
          <div className="hidden sm:block">
            <span className="font-bold text-base tracking-tight">WaitTime Canada</span>
          </div>
          <span className="font-bold text-base sm:hidden">WTC</span>
        </Link>

        {/* Central Search Bar - Only shown when showStats is true */}
        {showStats && onSearchChange && (
          <div className="hidden sm:flex flex-1 max-w-md mx-4">
            <div className="relative w-full">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search hospitals..."
                className="w-full pl-9 pr-8 py-2 rounded-lg border border-border bg-muted/30 focus:bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-200 outline-none text-sm"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
              />
              {searchQuery && (
                <button
                  onClick={() => onSearchChange("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {/* Right side controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {viewMode && onViewModeChange && (
            <>
              <ViewToggle mode={viewMode} onChange={onViewModeChange} />
              <div className="w-px h-5 bg-border hidden sm:block" />
            </>
          )}
          <nav className="hidden md:flex items-center text-sm font-medium">
            <Link 
              href="/faq" 
              className="px-2.5 py-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-200"
            >
              FAQ
            </Link>
          </nav>
          <ThemeToggle />
        </div>
      </div>

      {/* Stats Bar - Only shown when showStats is true */}
      {showStats && (
        <div className="border-t border-border/30 bg-muted/20">
          <div className="container flex items-center justify-between px-4 sm:px-6 py-2 gap-4">
            {/* Stats */}
            <div className="flex items-center gap-4 text-xs sm:text-sm">
              <div className="flex items-center gap-1.5">
                <span className="text-muted-foreground">Hospitals:</span>
                <span className="font-semibold tabular-nums">{hospitalCount ?? "--"}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
                </span>
                <span className="text-muted-foreground">Live:</span>
                <span className="font-semibold text-success tabular-nums">{liveCount ?? "--"}</span>
              </div>
            </div>

            {/* Mobile Search - shown on small screens */}
            {onSearchChange && (
              <div className="flex sm:hidden flex-1 max-w-[200px]">
                <div className="relative w-full">
                  <svg
                    className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="text"
                    placeholder="Search..."
                    className="w-full pl-8 pr-2 py-1.5 rounded-md border border-border bg-background text-xs"
                    value={searchQuery}
                    onChange={(e) => onSearchChange(e.target.value)}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
