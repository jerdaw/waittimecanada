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
}

export const stakeholderTestimonials: StakeholderTestimonial[] = [];

export function getFeaturedTestimonial(): StakeholderTestimonial | null {
  return stakeholderTestimonials.find((testimonial) => testimonial.published) ?? null;
}
