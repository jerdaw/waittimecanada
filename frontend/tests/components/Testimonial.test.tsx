import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Testimonial } from "@/components/Testimonial";
import type { StakeholderTestimonial } from "@/content/stakeholderTestimonials";

describe("Testimonial", () => {
  it("renders a role-only attribution with context", () => {
    const testimonial: StakeholderTestimonial = {
      id: "t-1",
      quote: "The warning helps clarify that the numbers are not directly comparable.",
      role: "ER Nurse",
      organization: "Toronto General Hospital",
      province: "ON",
      attribution: "role_only",
      published: true,
    };

    render(<Testimonial testimonial={testimonial} />);

    expect(screen.getByText(/Stakeholder Feedback/i)).toBeInTheDocument();
    expect(screen.getByText(/The warning helps clarify/i)).toBeInTheDocument();
    expect(screen.getByText("ER Nurse")).toBeInTheDocument();
    expect(screen.getByText("Toronto General Hospital - ON")).toBeInTheDocument();
  });

  it("renders named attribution when approved", () => {
    const testimonial: StakeholderTestimonial = {
      id: "t-2",
      quote: "Methodology context should always be shown beside wait-time values.",
      role: "Emergency Physician",
      displayName: "Dr. Jane Doe",
      attribution: "named",
      published: true,
    };

    render(<Testimonial testimonial={testimonial} />);

    expect(screen.getByText("Dr. Jane Doe, Emergency Physician")).toBeInTheDocument();
  });

  it("renders anonymous attribution safely", () => {
    const testimonial: StakeholderTestimonial = {
      id: "t-3",
      quote: "Patients often do not realize the measurement definitions are different.",
      role: "ER Clinician",
      attribution: "anonymous",
      published: true,
    };

    render(<Testimonial testimonial={testimonial} />);

    expect(screen.getByText("Anonymous ER Clinician")).toBeInTheDocument();
  });

  it("does not render unpublished testimonials", () => {
    const testimonial: StakeholderTestimonial = {
      id: "t-4",
      quote: "This should never render publicly before publication approval.",
      role: "ER Nurse",
      attribution: "role_only",
      published: false,
    };

    const { container } = render(<Testimonial testimonial={testimonial} />);
    expect(container).toBeEmptyDOMElement();
  });
});
