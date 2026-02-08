export type TestimonialAttribution = "anonymous" | "role_only" | "named";

export interface StakeholderTestimonial {
  id: string;
  quote: string;
  role: string;
  displayName?: string;
  organization?: string;
  province?: string;
  attribution: TestimonialAttribution;
  published: boolean;
  publishedAt?: string;
  approvalReference?: string;
}

export const stakeholderTestimonials: StakeholderTestimonial[] = [];

const MIN_QUOTE_LENGTH = 24;
const MAX_QUOTE_LENGTH = 600;

export function validateStakeholderTestimonials(
  testimonials: StakeholderTestimonial[] = stakeholderTestimonials
): string[] {
  const errors: string[] = [];
  const seenIds = new Set<string>();
  const published = testimonials.filter((testimonial) => testimonial.published);

  if (published.length > 1) {
    errors.push(
      `Expected at most 1 published testimonial, found ${published.length}.`
    );
  }

  for (const testimonial of testimonials) {
    const id = testimonial.id.trim();
    if (!id) {
      errors.push("Encountered testimonial with empty id.");
      continue;
    }

    if (seenIds.has(id)) {
      errors.push(`Duplicate testimonial id '${id}'.`);
    }
    seenIds.add(id);

    if (!testimonial.quote.trim()) {
      errors.push(`Testimonial '${id}' has an empty quote.`);
    }

    if (!testimonial.role.trim()) {
      errors.push(`Testimonial '${id}' has an empty role.`);
    }

    if (testimonial.published) {
      const quoteLength = testimonial.quote.trim().length;
      if (quoteLength < MIN_QUOTE_LENGTH) {
        errors.push(
          `Published testimonial '${id}' quote is too short (${quoteLength} chars).`
        );
      }
      if (quoteLength > MAX_QUOTE_LENGTH) {
        errors.push(
          `Published testimonial '${id}' quote is too long (${quoteLength} chars).`
        );
      }

      if (!testimonial.approvalReference || !testimonial.approvalReference.trim()) {
        errors.push(`Published testimonial '${id}' is missing approvalReference.`);
      }

      if (!testimonial.publishedAt || Number.isNaN(Date.parse(testimonial.publishedAt))) {
        errors.push(
          `Published testimonial '${id}' is missing a valid publishedAt ISO timestamp.`
        );
      }
    }

    if (testimonial.attribution === "named") {
      if (!testimonial.displayName || !testimonial.displayName.trim()) {
        errors.push(
          `Named testimonial '${id}' requires a non-empty displayName.`
        );
      }
    } else if (testimonial.displayName) {
      errors.push(
        `Testimonial '${id}' should not include displayName unless attribution is 'named'.`
      );
    }
  }

  return errors;
}

export function getFeaturedTestimonial(): StakeholderTestimonial | null {
  const validationErrors = validateStakeholderTestimonials(stakeholderTestimonials);
  if (validationErrors.length > 0) {
    console.error(
      "[stakeholderTestimonials] Validation failed. No testimonial will be rendered.",
      validationErrors
    );
    return null;
  }

  return stakeholderTestimonials.find((testimonial) => testimonial.published) ?? null;
}
