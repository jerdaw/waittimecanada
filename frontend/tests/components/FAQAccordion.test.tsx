import { render, screen, fireEvent } from "@testing-library/react";
import { FAQAccordion } from "@/components/FAQAccordion";

const items = [
  { question: "Question 1", answer: "Answer 1" },
  { question: "Question 2", answer: "Answer 2" },
];

describe("FAQAccordion", () => {
  it("renders all questions", () => {
    render(<FAQAccordion items={items} />);
    expect(screen.getByText("Question 1")).toBeInTheDocument();
    expect(screen.getByText("Question 2")).toBeInTheDocument();
  });

  it("expands item on click", () => {
    render(<FAQAccordion items={items} />);
    
    // Initial state: answers are not fully visible (CSS hidden)
    // Note: getByText finds them in DOM.
    expect(screen.getByText("Answer 1")).toBeInTheDocument();
    
    const button = screen.getByText("Question 1").closest("button");
    fireEvent.click(button!);
    
    // Check if aria-expanded is true
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  it("collapses other items when opening new one", () => {
    render(<FAQAccordion items={items} />);
    
    const button1 = screen.getByText("Question 1").closest("button");
    const button2 = screen.getByText("Question 2").closest("button");
    
    fireEvent.click(button1!);
    expect(button1).toHaveAttribute("aria-expanded", "true");
    
    fireEvent.click(button2!);
    expect(button2).toHaveAttribute("aria-expanded", "true");
    expect(button1).toHaveAttribute("aria-expanded", "false");
  });

  it("toggles same item on click", () => {
    render(<FAQAccordion items={items} />);
    const button = screen.getByText("Question 1").closest("button");
    
    fireEvent.click(button!);
    expect(button).toHaveAttribute("aria-expanded", "true");
    
    fireEvent.click(button!);
    expect(button).toHaveAttribute("aria-expanded", "false");
  });
});
