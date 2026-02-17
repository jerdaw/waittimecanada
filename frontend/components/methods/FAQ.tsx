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
        <h3 className="text-2xl font-bold text-slate-900 mb-2">
          {t('title')}
        </h3>
        <p className="text-slate-600">
          {t('subtitle')}
        </p>
      </div>

      <div className="space-y-3">
        {faqs.map((faq, index) => {
          const isExpanded = expandedIndex === index;

          return (
            <div
              key={index}
              className="border border-slate-200 rounded-lg overflow-hidden bg-white hover:border-blue-300 transition-colors"
            >
              <button
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-50 transition-colors"
              >
                <span className="font-medium text-slate-900 pr-4">
                  {faq.question}
                </span>
                <svg
                  className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
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
                <div className="px-6 pb-4 text-slate-700 leading-relaxed border-t border-slate-200 pt-4 bg-slate-50">
                  {faq.answer}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Contact CTA */}
      <div className="mt-8 p-6 rounded-xl bg-blue-50 border border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-2">
          {t('cta.title')}
        </h4>
        <p className="text-blue-800 text-sm mb-4">
          {t('cta.description')}
        </p>
        <a
          href="https://github.com/jerdaw/waittimecanada/issues"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
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
