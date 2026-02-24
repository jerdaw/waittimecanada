import { useTranslations } from "next-intl";

const PROVINCES = [
  { code: "ON", key: "on" as const },
  { code: "QC", key: "qc" as const },
  { code: "AB", key: "ab" as const },
  { code: "BC", key: "bc" as const },
];

export function ProvinceCoverage() {
  const t = useTranslations("Hero");

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-350">
      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3 text-center lg:text-left">
        {t("provinces.title")}
      </p>
      <div className="flex flex-wrap gap-2 justify-center lg:justify-start">
        {PROVINCES.map(({ code, key }) => (
          <div
            key={code}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/60 border border-border/50 text-xs"
          >
            <span className="font-bold text-primary">{code}</span>
            <span className="text-muted-foreground">{t(`provinces.${key}`)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
