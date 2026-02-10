"use client";

import { useState } from "react";

const faqs = [
  {
    question: "Why can't I compare Ottawa and Gatineau directly?",
    answer:
      "Ottawa (Ontario) and Gatineau (Quebec) use different measurement methodologies. Ontario reports 90th percentile triage-to-physician time, while Quebec reports rolling average registration-to-provider time. These differences mean direct comparison would be statistically invalid. Our platform displays a methodology divergence warning when you attempt such comparisons.",
  },
  {
    question: "What does '90th percentile' mean in practice?",
    answer:
      "A P90 wait time of 120 minutes means that 90% of patients are seen faster than 2 hours, and only 10% wait longer. This is a conservative estimate used for worst-case planning. It's higher than the median (typical) wait time because it accounts for outliers and busy periods.",
  },
  {
    question: "Why do some hospitals show 'No Data'?",
    answer:
      "Hospitals show 'No Data' when: (1) The scraper hasn't run recently (technical issue), (2) The source hospital hasn't reported data, or (3) The hospital was recently added and awaits verification. Our heartbeat monitoring system tracks data freshness and displays a warning when data is stale.",
  },
  {
    question: "How often is this data updated?",
    answer:
      "Update frequency varies by province. Ontario sources update every 15 minutes, Quebec updates hourly. Our scrapers run automatically via GitHub Actions on 15-minute intervals. You can see the last update timestamp in the top-left corner of the map.",
  },
  {
    question: "Where does this data come from?",
    answer:
      "We aggregate data from official provincial sources: ER Watch for Ontario (which consolidates Ontario Health data), Index Santé for Quebec (which uses MSSS data), and official health authority portals for other provinces. All sources are documented in our methodology pages with links to original sources.",
  },
  {
    question: "What if I need medical help right now?",
    answer:
      "This is an informational tool for planning purposes only, not for emergency triage. If you have a medical emergency, call 911 immediately. For urgent but non-emergency care advice, call your provincial health line: Health811 in Ontario, Info-Santé 811 in Quebec, or Health Link 811 in Alberta/other provinces.",
  },
  {
    question: "Can I use this data for research or journalism?",
    answer:
      "Yes, all data displayed is from public sources. We encourage responsible use for research, journalism, and advocacy. Please attribute data to the original provincial sources and cite our methodology documentation. Contact us if you need bulk data access or have questions about our ontology system.",
  },
  {
    question: "Why are methodology differences important?",
    answer:
      "Healthcare systems are complex, and measurement choices affect outcomes. A province that reports triage-to-physician time is measuring something fundamentally different than one reporting registration-to-provider time. Without understanding these differences, comparisons can be misleading and policy decisions can be based on faulty data. Our platform makes these differences explicit.",
  },
];

export function FAQ() {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-slate-900 mb-2">
          Frequently Asked Questions
        </h3>
        <p className="text-slate-600">
          Common questions about wait time data and methodology
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
          Have more questions?
        </h4>
        <p className="text-blue-800 text-sm mb-4">
          We&apos;re continuously improving our methodology documentation and
          data sources. If you have questions or feedback, we&apos;d love to
          hear from you.
        </p>
        <a
          href="https://github.com/jerdaw/waittimecanada/issues"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Submit feedback on GitHub
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
