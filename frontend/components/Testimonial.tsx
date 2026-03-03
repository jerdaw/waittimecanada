import type { StakeholderTestimonial } from "@/content/stakeholderTestimonials";
import { useTranslations } from "next-intl";

interface TestimonialProps {
  testimonial: StakeholderTestimonial;
}

export function Testimonial({ testimonial }: TestimonialProps) {
  const t = useTranslations("Testimonial");

  if (!testimonial.published) {
    return null;
  }

  const getAttributionLabel = (testimonial: StakeholderTestimonial): string => {
    if (testimonial.attribution === "named" && testimonial.displayName) {
      return `${testimonial.displayName}, ${testimonial.role}`;
    }

    if (testimonial.attribution === "anonymous") {
      return `${t("anonymous")} ${testimonial.role}`;
    }

    return testimonial.role;
  };

  const getContextLabel = (
    testimonial: StakeholderTestimonial,
  ): string | null => {
    const parts = [testimonial.organization, testimonial.province].filter(
      Boolean,
    );
    return parts.length > 0 ? parts.join(" - ") : null;
  };

  const attribution = getAttributionLabel(testimonial);
  const context = getContextLabel(testimonial);

  return (
    <section className="rounded-xl border border-border/50 bg-card p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary">
        {t("label")}
      </p>
      <blockquote className="mt-3 text-sm leading-relaxed text-foreground">
        &ldquo;{testimonial.quote}&rdquo;
      </blockquote>
      <footer className="mt-4 border-t border-border/60 pt-3">
        <p className="text-sm font-medium text-foreground">{attribution}</p>
        {context && <p className="text-xs text-muted-foreground">{context}</p>}
      </footer>
    </section>
  );
}
