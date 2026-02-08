import { describe, expect, it } from "vitest";

import {
  getFeaturedTestimonial,
  stakeholderTestimonials,
  validateStakeholderTestimonials,
  type StakeholderTestimonial,
} from "@/content/stakeholderTestimonials";

function buildTestimonial(
  partial: Partial<StakeholderTestimonial> = {}
): StakeholderTestimonial {
  return {
    id: "t-1",
    quote:
      "Methodology warnings are useful because patients often assume all wait-time numbers are equivalent.",
    role: "ER Nurse",
    attribution: "role_only",
    published: false,
    ...partial,
  };
}

describe("stakeholderTestimonials governance", () => {
  it("allows a valid single published testimonial", () => {
    const testimonials: StakeholderTestimonial[] = [
      buildTestimonial({
        published: true,
        publishedAt: "2026-02-08T00:00:00.000Z",
        approvalReference: "docs/stakeholder-feedback.md#interview-1",
      }),
    ];

    expect(validateStakeholderTestimonials(testimonials)).toEqual([]);
  });

  it("rejects more than one published testimonial", () => {
    const testimonials: StakeholderTestimonial[] = [
      buildTestimonial({
        id: "t-1",
        published: true,
        publishedAt: "2026-02-08T00:00:00.000Z",
        approvalReference: "ref-1",
      }),
      buildTestimonial({
        id: "t-2",
        published: true,
        publishedAt: "2026-02-08T00:00:00.000Z",
        approvalReference: "ref-2",
      }),
    ];

    const errors = validateStakeholderTestimonials(testimonials);
    expect(errors.some((error) => error.includes("at most 1 published"))).toBe(true);
  });

  it("requires governance metadata for published testimonials", () => {
    const testimonials: StakeholderTestimonial[] = [
      buildTestimonial({ published: true }),
    ];

    const errors = validateStakeholderTestimonials(testimonials);
    expect(errors.some((error) => error.includes("approvalReference"))).toBe(true);
    expect(errors.some((error) => error.includes("publishedAt"))).toBe(true);
  });

  it("requires displayName for named attribution", () => {
    const testimonials: StakeholderTestimonial[] = [
      buildTestimonial({
        attribution: "named",
        published: true,
        publishedAt: "2026-02-08T00:00:00.000Z",
        approvalReference: "ref-1",
      }),
    ];

    const errors = validateStakeholderTestimonials(testimonials);
    expect(errors.some((error) => error.includes("requires a non-empty displayName"))).toBe(true);
  });

  it("keeps the repository dataset valid by default", () => {
    expect(validateStakeholderTestimonials(stakeholderTestimonials)).toEqual([]);
    expect(getFeaturedTestimonial()).toBeNull();
  });
});
