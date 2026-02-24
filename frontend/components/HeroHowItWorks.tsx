import { MapPin, Clock, BookOpen } from "lucide-react";
import { useTranslations } from "next-intl";

export function HeroHowItWorks() {
  const t = useTranslations("Hero");

  const steps = [
    {
      icon: MapPin,
      title: t("howItWorks.step1.title"),
      desc: t("howItWorks.step1.desc"),
    },
    {
      icon: Clock,
      title: t("howItWorks.step2.title"),
      desc: t("howItWorks.step2.desc"),
    },
    {
      icon: BookOpen,
      title: t("howItWorks.step3.title"),
      desc: t("howItWorks.step3.desc"),
    },
  ];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-400">
      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4">
        {t("howItWorks.title")}
      </p>
      <div className="flex flex-col gap-3">
        {steps.map((step, i) => {
          const Icon = step.icon;
          return (
            <div key={step.title} className="flex items-start gap-3">
              <div className="relative flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-primary/15 border border-primary/20 flex items-center justify-center">
                  <Icon className="w-4 h-4 text-primary" aria-hidden="true" />
                </div>
                {i < steps.length - 1 && (
                  <div className="absolute top-8 left-1/2 -translate-x-1/2 w-px h-3 bg-border/50" />
                )}
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground leading-tight">
                  {step.title}
                </p>
                <p className="text-sm text-muted-foreground mt-0.5 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
