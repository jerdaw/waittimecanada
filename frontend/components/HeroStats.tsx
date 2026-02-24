import { useTranslations } from "next-intl";

interface HeroStatsProps {
  hospitalCount: number;
}

export function HeroStats({ hospitalCount }: HeroStatsProps) {
  const t = useTranslations("Hero");

  const stats = [
    { label: t("stats.provinces") },
    { label: t("stats.hospitals", { count: hospitalCount > 0 ? hospitalCount : "..." }) },
    { label: t("stats.cadence") },
  ];

  return (
    <div className="hero-stats-bar flex flex-wrap gap-3 justify-center lg:justify-start animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
      {stats.map((stat) => (
        <span
          key={stat.label}
          className="px-3 py-1 rounded-full bg-muted/60 border border-border/40 text-xs font-medium text-muted-foreground"
        >
          {stat.label}
        </span>
      ))}
    </div>
  );
}
