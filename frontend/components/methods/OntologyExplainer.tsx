"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

export function OntologyExplainer() {
  const t = useTranslations('Methods.OntologyExplainer');
  const [expandedDimension, setExpandedDimension] = useState<number | null>(0);

  const dimensions = [
    {
      title: t('dimensions.metricFamily.title'),
      subtitle: t('dimensions.metricFamily.subtitle'),
      description: t('dimensions.metricFamily.description'),
      examples: [
        {
          value: "TIME_TO_PROVIDER",
          label: t('dimensions.metricFamily.examples.timeToProvider.label'),
          explanation: t('dimensions.metricFamily.examples.timeToProvider.explanation'),
        },
        {
          value: "TOTAL_LOS",
          label: t('dimensions.metricFamily.examples.totalLos.label'),
          explanation: t('dimensions.metricFamily.examples.totalLos.explanation'),
        },
        {
          value: "STRETCHER_OCCUPANCY",
          label: t('dimensions.metricFamily.examples.stretcherOccupancy.label'),
          explanation: t('dimensions.metricFamily.examples.stretcherOccupancy.explanation'),
        },
      ],
    },
    {
      title: t('dimensions.startEvent.title'),
      subtitle: t('dimensions.startEvent.subtitle'),
      description: t('dimensions.startEvent.description'),
      examples: [
        {
          value: "DOOR",
          label: t('dimensions.startEvent.examples.door.label'),
          explanation: t('dimensions.startEvent.examples.door.explanation'),
        },
        {
          value: "TRIAGE",
          label: t('dimensions.startEvent.examples.triage.label'),
          explanation: t('dimensions.startEvent.examples.triage.explanation'),
        },
        {
          value: "REGISTRATION",
          label: t('dimensions.startEvent.examples.registration.label'),
          explanation: t('dimensions.startEvent.examples.registration.explanation'),
        },
      ],
    },
    {
      title: t('dimensions.endEvent.title'),
      subtitle: t('dimensions.endEvent.subtitle'),
      description: t('dimensions.endEvent.description'),
      examples: [
        {
          value: "PHYSICIAN",
          label: t('dimensions.endEvent.examples.physician.label'),
          explanation: t('dimensions.endEvent.examples.physician.explanation'),
        },
        {
          value: "PROVIDER",
          label: t('dimensions.endEvent.examples.provider.label'),
          explanation: t('dimensions.endEvent.examples.provider.explanation'),
        },
        {
          value: "DISCHARGE",
          label: t('dimensions.endEvent.examples.discharge.label'),
          explanation: t('dimensions.endEvent.examples.discharge.explanation'),
        },
      ],
    },
    {
      title: t('dimensions.statisticType.title'),
      subtitle: t('dimensions.statisticType.subtitle'),
      description: t('dimensions.statisticType.description'),
      examples: [
        {
          value: "P90",
          label: t('dimensions.statisticType.examples.p90.label'),
          explanation: t('dimensions.statisticType.examples.p90.explanation'),
        },
        {
          value: "MEDIAN",
          label: t('dimensions.statisticType.examples.median.label'),
          explanation: t('dimensions.statisticType.examples.median.explanation'),
        },
        {
          value: "ROLLING_AVG",
          label: t('dimensions.statisticType.examples.rollingAvg.label'),
          explanation: t('dimensions.statisticType.examples.rollingAvg.explanation'),
        },
        {
          value: "POINT_ESTIMATE",
          label: t('dimensions.statisticType.examples.pointEstimate.label'),
          explanation: t('dimensions.statisticType.examples.pointEstimate.explanation'),
        },
      ],
    },
  ];

  return (
    <div className="space-y-4">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-foreground mb-2">
          {t('title')}
        </h3>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          {t('subtitle')}
        </p>
      </div>

      {dimensions.map((dimension, index) => {
        const isExpanded = expandedDimension === index;

        return (
          <div
            key={index}
            className="border-2 border-border rounded-xl overflow-hidden bg-card transition-all duration-200 hover:border-primary/40"
          >
            {/* Header - Always visible */}
            <button
              onClick={() => setExpandedDimension(isExpanded ? null : index)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-lg">
                  {index + 1}
                </div>
                <div className="text-left">
                  <h4 className="font-semibold text-foreground text-lg">
                    {dimension.title}
                  </h4>
                  <p className="text-sm text-muted-foreground">{dimension.subtitle}</p>
                </div>
              </div>
              <svg
                className={`w-6 h-6 text-muted-foreground transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
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
              <div className="px-6 pb-6 border-t border-border bg-muted/30">
                <p className="text-muted-foreground mb-4 pt-4">
                  {dimension.description}
                </p>

                <div className="space-y-3">
                  {dimension.examples.map((example, exIndex) => (
                    <div
                      key={exIndex}
                      className="p-4 rounded-lg bg-card border border-border"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <span className="font-semibold text-foreground">
                            {example.label}
                          </span>
                          <code className="ml-2 px-2 py-0.5 rounded bg-muted text-xs text-muted-foreground font-mono">
                            {example.value}
                          </code>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {example.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Summary callout */}
      <div className="mt-8 p-6 rounded-xl bg-primary/5 border-2 border-primary/20">
        <div className="flex gap-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
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
            <h4 className="font-semibold text-foreground mb-2">
              {t('summary.title')}
            </h4>
            <p className="text-muted-foreground text-sm leading-relaxed">
              {t('summary.description')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
