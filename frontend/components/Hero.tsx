import type { Hospital } from "@/app/api/hospitals/route";
import { clsx } from "clsx";
import Link from "next/link";
import { calculateDistance } from "@/utils/distance";
import { useTranslations } from "next-intl";
import { HeroStats } from "@/components/HeroStats";
import { HeroHowItWorks } from "@/components/HeroHowItWorks";
import { ProvinceCoverage } from "@/components/ProvinceCoverage";

const PROVINCES = ["ON", "QC", "AB", "BC"] as const;
type ProvinceCode = (typeof PROVINCES)[number];

interface HeroProps {
  hospitals: Hospital[];
  onExplore: () => void;
  className?: string;
  userLocation?: { lat: number; lon: number } | null;
  loading?: boolean;
  selectedProvince?: string;
  onProvinceChange?: (province: string) => void;
  onSelectHospital?: (id: string) => void;
}

export function Hero({
  hospitals,
  onExplore,
  className,
  userLocation,
  loading,
  selectedProvince,
  onProvinceChange,
  onSelectHospital,
}: HeroProps) {
  const t = useTranslations('Hero');

  // Find the featured hospital based on location
  const featuredHospital = (() => {
    const hospitalsWithData = hospitals.filter(
      (h) => h.current_wait_time !== null && h.current_wait_time !== undefined,
    );

    if (hospitalsWithData.length === 0) return null;

    // If we have location, show the nearest hospital
    if (userLocation) {
      const sorted = [...hospitalsWithData].sort((a, b) => {
        const distA = calculateDistance(
          userLocation.lat,
          userLocation.lon,
          a.latitude,
          a.longitude,
        );
        const distB = calculateDistance(
          userLocation.lat,
          userLocation.lon,
          b.latitude,
          b.longitude,
        );
        return distA - distB;
      });
      return {
        hospital: sorted[0],
        type: "nearest" as const,
        distance: calculateDistance(
          userLocation.lat,
          userLocation.lon,
          sorted[0].latitude,
          sorted[0].longitude,
        ),
      };
    }

    // Otherwise show shortest wait (fallback)
    const sorted = [...hospitalsWithData].sort(
      (a, b) => (a.current_wait_time ?? 999) - (b.current_wait_time ?? 999),
    );
    return { hospital: sorted[0], type: "shortest" as const, distance: null };
  })();

  const formatDistance = (km: number) => {
    if (km < 1) return `${Math.round(km * 1000)}m`;
    return `${km.toFixed(1)}km`;
  };

  return (
    <section
      className={clsx(
        "relative py-8 px-6 md:py-12 lg:py-14 overflow-hidden min-h-[40vh] flex items-center",
        "bg-gradient-to-b from-muted/30 via-background to-background",
        className,
      )}
    >
      {/* Subtle dot grid pattern */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.15] dark:opacity-[0.15]"
        style={{
          backgroundImage:
            "radial-gradient(circle, var(--muted-foreground) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* Soft gradient overlays for depth */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
        {/* Subtle vignette */}
        <div className="absolute inset-0 bg-gradient-to-r from-background/50 via-transparent to-background/50" />
      </div>

      <div className="container max-w-6xl mx-auto flex flex-col lg:flex-row items-center gap-12 lg:gap-20 relative">
        <div className="flex-1 text-center lg:text-left space-y-6">
          {/* Badge pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-semibold animate-in fade-in slide-in-from-bottom-4 duration-700 border border-primary/20">
            <span className="relative flex h-2 w-2" aria-hidden="true">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            {t('badge')}
          </div>

          {/* Stats bar */}
          <HeroStats hospitalCount={hospitals.length} />

          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground animate-in fade-in slide-in-from-bottom-5 duration-700 delay-100">
            {t('title')} <span className="text-primary">{t('subtitle')}</span> <br />
            {t('subtitle2')}
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto lg:mx-0 animate-in fade-in slide-in-from-bottom-6 duration-700 delay-200 leading-relaxed">
            {t('description', {count: hospitals.length || "..."})}
          </p>

          {/* Province quick-pick */}
          {onProvinceChange && (
            <div className="flex flex-wrap gap-2 justify-center lg:justify-start animate-in fade-in slide-in-from-bottom-6 duration-700 delay-300">
              {PROVINCES.map((province) => (
                <button
                  key={province}
                  onClick={() => onProvinceChange(province)}
                  className={clsx(
                    "px-4 py-1.5 rounded-full text-sm font-semibold border transition-all duration-150",
                    selectedProvince === province
                      ? "bg-primary text-primary-foreground border-primary shadow-sm shadow-primary/20"
                      : "bg-muted/60 text-muted-foreground border-border/40 hover:border-primary/40 hover:text-foreground",
                  )}
                  aria-pressed={selectedProvince === province}
                >
                  {province}
                </button>
              ))}
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-center gap-5 justify-center lg:justify-start animate-in fade-in slide-in-from-bottom-7 duration-700 delay-300 pt-2">
            <button
              onClick={onExplore}
              aria-label={t('cta.explore')}
              className="group px-8 py-3.5 bg-primary text-primary-foreground rounded-full font-semibold shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:bg-primary-hover hover:scale-[1.02] transition-all duration-200 active:scale-[0.98]"
            >
              <span className="flex items-center gap-2">
                {t('cta.explore')}
                <svg
                  className="w-5 h-5 group-hover:translate-x-0.5 transition-transform"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 8l4 4m0 0l-4 4m4-4H3"
                  />
                </svg>
              </span>
            </button>
            <Link
              href="/methods"
              className="text-muted-foreground hover:text-foreground font-medium flex items-center gap-1.5 transition-colors"
            >
              {t('cta.methodologies')}
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          </div>

          {/* Province coverage strip */}
          <ProvinceCoverage />

          {/* How It Works — desktop only */}
          <div className="hidden lg:block pt-2 border-t border-border/30">
            <HeroHowItWorks />
          </div>
        </div>

        {/* Featured Hospital Card - Floating widget style */}
        <div className="w-full max-w-sm lg:w-[400px] animate-in fade-in slide-in-from-right-10 duration-1000 delay-300">
          <button
            type="button"
            className="relative group w-full text-left"
            onClick={() => {
              if (featuredHospital) {
                onSelectHospital?.(featuredHospital.hospital.id);
                onExplore();
              }
            }}
            aria-label={featuredHospital ? `${t('card.explore')}: ${featuredHospital.hospital.name}` : undefined}
          >
            {/* Enhanced card glow effect for floating appearance */}
            <div className="absolute -inset-2 bg-gradient-to-r from-primary/25 via-accent/20 to-primary/25 rounded-3xl blur-2xl opacity-40 group-hover:opacity-60 transition-opacity duration-500" />

            <div className="relative bg-card rounded-2xl shadow-2xl border border-border/40 overflow-hidden group-hover:border-primary/30 transition-colors">
              {/* Gradient top bar */}
              <div className="h-1 bg-gradient-to-r from-primary via-accent to-primary" />

              <div className="p-7">
                <div className="flex justify-between items-center mb-6">
                  <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                    {featuredHospital?.type === "nearest"
                      ? t('card.nearest')
                      : featuredHospital?.type === "shortest"
                        ? t('card.shortest')
                        : t('card.featured')}
                  </span>
                  <span className="flex items-center gap-1.5 text-success bg-success/10 px-2.5 py-1 rounded-full text-xs font-bold ring-1 ring-inset ring-success/20">
                    <span className="relative flex h-1.5 w-1.5" aria-hidden="true">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-success" />
                    </span>
                    {t('card.live')}
                  </span>
                </div>

                {!loading && featuredHospital ? (
                  <div className="space-y-4">
                    <div>
                      <h2 className="text-xl font-bold text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                        {featuredHospital.hospital.name}
                      </h2>
                      <div className="flex items-center gap-2 text-sm mt-0.5">
                        <span className="text-muted-foreground">
                          {featuredHospital.hospital.city},{" "}
                          {featuredHospital.hospital.province}
                        </span>
                        {featuredHospital.distance !== null && (
                          <span className="text-xs bg-muted px-2 py-0.5 rounded-full font-medium">
                            {formatDistance(featuredHospital.distance)}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-black text-foreground tracking-tight tabular-nums">
                        {Math.round(
                          featuredHospital.hospital.current_wait_time ?? 0,
                        )}
                      </span>
                      <span className="text-xl font-medium text-muted-foreground">
                        {t('card.min')}
                      </span>
                    </div>

                    <div className="pt-4 border-t border-border/50">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className="flex items-center gap-1.5">
                          <span className="w-1 h-1 rounded-full bg-success" aria-hidden="true" />
                          {t(`card.statisticType.${featuredHospital.hospital.statistic_type ?? 'P90'}`)}
                        </span>
                        {featuredHospital.hospital.metric_family && (
                          <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium border border-primary/15">
                            {t('card.methodology')}: {featuredHospital.hospital.metric_family.replace(/_/g, ' ')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-40 space-y-3 text-muted-foreground">
                    <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" aria-hidden="true" />
                    <span className="text-sm">{t('card.loading')}</span>
                  </div>
                )}
              </div>
            </div>
          </button>
        </div>
      </div>
    </section>
  );
}
