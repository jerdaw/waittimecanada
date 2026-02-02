"use client";

import { useState } from "react";

const dimensions = [
  {
    title: "Metric Family",
    subtitle: "What is being measured?",
    description:
      "The fundamental category of measurement. Different metric families answer different clinical questions.",
    examples: [
      {
        value: "TIME_TO_PROVIDER",
        label: "Time to Provider",
        explanation: "How long until a patient is first assessed by a healthcare provider",
      },
      {
        value: "TOTAL_LOS",
        label: "Total Length of Stay",
        explanation: "Complete duration from arrival to discharge from the ED",
      },
      {
        value: "STRETCHER_OCCUPANCY",
        label: "Stretcher Occupancy",
        explanation: "Percentage of available stretcher beds currently occupied",
      },
    ],
  },
  {
    title: "Start Event",
    subtitle: "When does the clock start?",
    description:
      "The triggering event that begins the measurement. This can significantly affect reported times.",
    examples: [
      {
        value: "DOOR",
        label: "Door (Arrival)",
        explanation: "Clock starts when patient physically enters the ED",
      },
      {
        value: "TRIAGE",
        label: "Triage",
        explanation: "Clock starts when triage nurse assessment is completed",
      },
      {
        value: "REGISTRATION",
        label: "Registration",
        explanation: "Clock starts when administrative check-in is completed",
      },
    ],
  },
  {
    title: "End Event",
    subtitle: "When does the clock stop?",
    description:
      "The event that concludes the measurement. Differences here can make provinces incomparable.",
    examples: [
      {
        value: "PHYSICIAN",
        label: "Physician Contact",
        explanation: "Clock stops when patient first sees a medical doctor",
      },
      {
        value: "PROVIDER",
        label: "Any Provider Contact",
        explanation:
          "Clock stops at first contact with MD, nurse practitioner, or physician assistant",
      },
      {
        value: "DISCHARGE",
        label: "Discharge",
        explanation: "Clock stops when patient leaves the ED",
      },
    ],
  },
  {
    title: "Statistic Type",
    subtitle: "How is the number calculated?",
    description:
      "The mathematical method used to aggregate individual wait times. This profoundly affects interpretation.",
    examples: [
      {
        value: "P90",
        label: "90th Percentile",
        explanation: "90% of patients are seen faster than this time (worst-case planning)",
      },
      {
        value: "MEDIAN",
        label: "Median (50th Percentile)",
        explanation: "Typical middle-of-the-road experience for an average patient",
      },
      {
        value: "ROLLING_AVG",
        label: "Rolling Average",
        explanation: "Smoothed average over recent time period, reduces noise",
      },
      {
        value: "POINT_ESTIMATE",
        label: "Real-Time Estimate",
        explanation: "Current snapshot based on current conditions and queue",
      },
    ],
  },
];

export function OntologyExplainer() {
  const [expandedDimension, setExpandedDimension] = useState<number | null>(0);

  return (
    <div className="space-y-4">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-slate-900 mb-2">
          The Four Dimensions of Wait Time Measurement
        </h3>
        <p className="text-slate-600 max-w-2xl mx-auto">
          For two measurements to be comparable, all four dimensions must match.
          Understanding these dimensions is crucial for interpreting published wait times.
        </p>
      </div>

      {dimensions.map((dimension, index) => {
        const isExpanded = expandedDimension === index;

        return (
          <div
            key={index}
            className="border-2 border-slate-200 rounded-xl overflow-hidden bg-white transition-all duration-200 hover:border-blue-300"
          >
            {/* Header - Always visible */}
            <button
              onClick={() => setExpandedDimension(isExpanded ? null : index)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-lg">
                  {index + 1}
                </div>
                <div className="text-left">
                  <h4 className="font-semibold text-slate-900 text-lg">
                    {dimension.title}
                  </h4>
                  <p className="text-sm text-slate-500">{dimension.subtitle}</p>
                </div>
              </div>
              <svg
                className={`w-6 h-6 text-slate-400 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
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

            {/* Expanded content */}
            {isExpanded && (
              <div className="px-6 pb-6 border-t border-slate-200 bg-slate-50">
                <p className="text-slate-700 mb-4 pt-4">{dimension.description}</p>

                <div className="space-y-3">
                  {dimension.examples.map((example, exIndex) => (
                    <div
                      key={exIndex}
                      className="p-4 rounded-lg bg-white border border-slate-200"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <span className="font-semibold text-slate-900">
                            {example.label}
                          </span>
                          <code className="ml-2 px-2 py-0.5 rounded bg-slate-100 text-xs text-slate-600 font-mono">
                            {example.value}
                          </code>
                        </div>
                      </div>
                      <p className="text-sm text-slate-600">{example.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Summary callout */}
      <div className="mt-8 p-6 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200">
        <div className="flex gap-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center">
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-blue-900 mb-2">
              Why This Matters
            </h4>
            <p className="text-blue-800 text-sm leading-relaxed">
              A 60-minute wait in Ontario (P90, Triage→Physician) is fundamentally
              different from a 60-minute wait in Quebec (Rolling Avg,
              Registration→Provider). Our platform automatically detects these
              differences and warns you when comparing incompatible measurements.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
