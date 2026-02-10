import type { StakeholderTestimonial } from "@/content/stakeholderTestimonials";

interface TestimonialProps {
  testimonial: StakeholderTestimonial;
}

function attributionLabel(testimonial: StakeholderTestimonial): string {
  if (testimonial.attribution === "named" && testimonial.displayName) {
    return `${testimonial.displayName}, ${testimonial.role}`;
  }

  if (testimonial.attribution === "anonymous") {
    return `Anonymous ${testimonial.role}`;
  }

  return testimonial.role;
}

function contextLabel(testimonial: StakeholderTestimonial): string | null {
  const parts = [testimonial.organization, testimonial.province].filter(
    Boolean,
  );
  return parts.length > 0 ? parts.join(" - ") : null;
}

export function Testimonial({ testimonial }: TestimonialProps) {
  if (!testimonial.published) {
    return null;
  }

  const attribution = attributionLabel(testimonial);
  const context = contextLabel(testimonial);

  return (
    <section className="rounded-xl border border-border/50 bg-card p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary">
        Stakeholder Feedback
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
