
import type { Hospital } from "@/app/api/hospitals/route";
import { clsx } from "clsx";

interface HeroProps {
  hospitals: Hospital[];
  onExplore: () => void;
  className?: string;
}

export function Hero({ hospitals, onExplore, className }: HeroProps) {
  // Find hospital with shortest valid wait time
  const shortestWait = hospitals
    .filter(
      (h) => h.current_wait_time !== null && h.current_wait_time !== undefined
    )
    .sort(
      (a, b) => (a.current_wait_time ?? 999) - (b.current_wait_time ?? 999)
    )[0];

  return (
    <section
      className={clsx(
        "relative py-12 px-4 md:py-20 lg:py-24 bg-gradient-to-b from-muted/50 to-background border-b border-border",
        className
      )}
    >
      <div className="container max-w-6xl mx-auto flex flex-col lg:flex-row items-center gap-10 lg:gap-16">
        <div className="flex-1 text-center lg:text-left space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium animate-in fade-in slide-in-from-bottom-4 duration-700">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            Real-Time Ontario ER Data
          </div>

          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground animate-in fade-in slide-in-from-bottom-5 duration-700 delay-100">
            Find the <span className="text-primary">Fastest ER</span> <br />
            Near You
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto lg:mx-0 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-200">
            Make informed decisions when every minute counts. View live wait times
            across <strong>{hospitals.length || "..."}</strong> Ontario hospitals
            instantly.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start animate-in fade-in slide-in-from-bottom-7 duration-700 delay-300">
            <button
              onClick={onExplore}
              className="px-8 py-3.5 bg-primary text-primary-foreground rounded-full font-semibold shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:scale-105 transition-all duration-200 active:scale-95"
            >
              Explore Hospitals
            </button>
            <a
              href="#"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              How data is collected →
            </a>
          </div>
        </div>

        {/* Live Preview Card */}
        <div className="w-full max-w-sm lg:w-[400px] animate-in fade-in slide-in-from-right-8 duration-1000 delay-200">
          <div className="bg-card rounded-3xl shadow-xl border border-border/50 p-6 relative overflow-hidden group hover:shadow-2xl transition-all duration-300">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-primary to-blue-500"></div>

            <div className="flex justify-between items-center mb-6">
              <span className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
                Shortest Wait Time
              </span>
              <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-500/10 px-2.5 py-1 rounded-full text-xs font-bold ring-1 ring-inset ring-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                LIVE
              </span>
            </div>

            {shortestWait ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-xl font-bold text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                    {shortestWait.name}
                  </h3>
                  <p className="text-muted-foreground text-sm">
                    {shortestWait.city}, {shortestWait.province}
                  </p>
                </div>

                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-foreground tracking-tight">
                    {Math.round(shortestWait.current_wait_time ?? 0)}
                  </span>
                  <span className="text-xl font-medium text-muted-foreground">
                    minutes
                  </span>
                </div>

                <div className="pt-4 border-t border-border">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>Performance (P90)</span>
                    <span>Updated just now</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-40 space-y-3 text-muted-foreground">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-sm">Finding fastest ER...</span>
              </div>
            )}
          </div>

          {/* Decorative elements behind card */}
          <div className="absolute -z-10 top-10 -right-10 w-40 h-40 bg-primary/20 rounded-full blur-3xl opacity-50"></div>
          <div className="absolute -z-10 -bottom-10 -left-10 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl opacity-50"></div>
        </div>
      </div>
    </section>
  );
}
