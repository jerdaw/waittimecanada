"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

export function FAQ() {
  const t = useTranslations('Methods.FAQ');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const faqs = [
    { question: t('items.q1.question'), answer: t('items.q1.answer') },
    { question: t('items.q2.question'), answer: t('items.q2.answer') },
    { question: t('items.q3.question'), answer: t('items.q3.answer') },
    { question: t('items.q4.question'), answer: t('items.q4.answer') },
    { question: t('items.q5.question'), answer: t('items.q5.answer') },
    { question: t('items.q6.question'), answer: t('items.q6.answer') },
    { question: t('items.q7.question'), answer: t('items.q7.answer') },
    { question: t('items.q8.question'), answer: t('items.q8.answer') },
  ];

  return (
    <div className="space-y-4">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-foreground mb-2">
          {t('title')}
        </h3>
        <p className="text-muted-foreground">
          {t('subtitle')}
        </p>
      </div>

      <div className="space-y-3">
        {faqs.map((faq, index) => {
          const isExpanded = expandedIndex === index;

          return (
            <div
              key={index}
              className="border border-border rounded-lg overflow-hidden bg-card hover:border-primary/40 transition-colors"
            >
              <button
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-muted/50 transition-colors"
              >
                <span className="font-medium text-foreground pr-4">
                  {faq.question}
                </span>
                <svg
                  className={`w-5 h-5 text-muted-foreground flex-shrink-0 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {isExpanded && (
                <div className="px-6 pb-4 text-muted-foreground leading-relaxed border-t border-border pt-4 bg-muted/30">
                  {faq.answer}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Contact CTA */}
      <div className="mt-8 p-6 rounded-xl bg-primary/5 border border-primary/20">
        <h4 className="font-semibold text-foreground mb-2">
          {t('cta.title')}
        </h4>
        <p className="text-muted-foreground text-sm mb-4">
          {t('cta.description')}
        </p>
        <a
          href="https://github.com/jerdaw/waittimecanada/issues"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary-hover transition-colors"
        >
          {t('cta.button')}
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>
      </div>
    </div>
  );
}
