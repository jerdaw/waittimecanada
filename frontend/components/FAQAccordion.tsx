"use client";

import { useState } from "react";
import { clsx } from "clsx";
import { ChevronDown } from "lucide-react";

interface FAQItem {
  question: string;
  answer: React.ReactNode;
}

interface FAQAccordionProps {
  items: FAQItem[];
}

export function FAQAccordion({ items }: FAQAccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleItem = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className="space-y-4">
      {items.map((item, index) => {
        const isOpen = openIndex === index;
        return (
          <div
            key={index}
            className={clsx(
              "border rounded-lg bg-card overflow-hidden transition-all duration-200 shadow-sm hover:shadow-md",
              isOpen
                ? "border-l-4 border-l-primary border-border"
                : "border-border",
            )}
          >
            <button
              onClick={() => toggleItem(index)}
              className="w-full flex items-center justify-between p-4 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              aria-expanded={isOpen}
              aria-controls={`faq-answer-${index}`}
            >
              <h3 className="font-semibold text-foreground pr-4">
                {item.question}
              </h3>
              <ChevronDown
                className={clsx(
                  "w-5 h-5 text-muted-foreground transition-transform duration-300 flex-shrink-0",
                  isOpen && "rotate-180",
                )}
              />
            </button>
            <div
              id={`faq-answer-${index}`}
              className={clsx(
                "grid transition-[grid-template-rows] duration-300 ease-in-out",
                isOpen
                  ? "grid-rows-[1fr] opacity-100"
                  : "grid-rows-[0fr] opacity-0",
              )}
            >
              <div className="overflow-hidden">
                <div className="p-4 pt-0 text-muted-foreground leading-relaxed">
                  {item.answer}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
