import { useTranslations } from "next-intl";

import type { PublicCoverage } from "@/types/coverage";

interface HeroStatsProps {
  coverage: PublicCoverage | null;
}

export function HeroStats({ coverage }: HeroStatsProps) {
  const t = useTranslations("Hero");
  const hasCoverage =
    coverage !== null &&
    coverage.hospital_count > 0 &&
    coverage.province_count > 0;
  const coverageDate = hasCoverage ? coverage.generated_at.slice(0, 10) : null;

  const stats = [
    {
      key: "provinces",
      label: hasCoverage
        ? t("stats.provinces", { count: coverage.province_count })
        : t("stats.provincesUnavailable"),
    },
    {
      key: "hospitals",
      label: hasCoverage
        ? t("stats.hospitals", { count: coverage.hospital_count })
        : t("stats.hospitalsUnavailable"),
    },
    { key: "cadence", label: t("stats.cadence") },
  ];

  return (
    <div
      className="hero-stats-bar flex flex-wrap gap-3 justify-center lg:justify-start animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100"
      aria-label={stats.map((stat) => stat.label).join(". ")}
    >
      {stats.map((stat) => (
        <span
          key={stat.key}
          className="px-3 py-1 rounded-full bg-muted/60 border border-border/40 text-xs font-medium text-muted-foreground"
        >
          {stat.label}
        </span>
      ))}
      {coverageDate && (
        <span className="sr-only">
          {t("stats.coverageAsOf", { date: coverageDate })}
        </span>
      )}
    </div>
  );
}
