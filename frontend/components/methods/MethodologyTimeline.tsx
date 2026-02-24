"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";

interface MethodologyEvent {
  id: number;
  source_id: string;
  detected_at: string;
  previous_period: {
    start: string;
    end: string;
    mean: number;
  };
  current_period: {
    start: string;
    end: string;
    mean: number;
  };
  shift_percent: number;
  hospitals_analyzed: number;
  explanation: string;
}

interface MethodologyTimelineProps {
  sources?: Array<{ id: string; name: string; province: string }>;
}

export function MethodologyTimeline({
  sources = [],
}: MethodologyTimelineProps) {
  const t = useTranslations('Methods.MethodologyTimeline');
  const [events, setEvents] = useState<MethodologyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<string>("all");

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const url =
          selectedSource === "all"
            ? "/api/methodology?limit=50"
            : `/api/methodology?source_id=${selectedSource}&limit=50`;

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error("Failed to fetch methodology changes");
        }

        const data = await response.json();
        setEvents(data.events || []);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [selectedSource]);

  // Helper to get source name from ID
  const getSourceName = (sourceId: string) => {
    const source = sources.find((s) => s.id === sourceId);
    return source ? source.province : sourceId;
  };

  // Helper to format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-danger">
        {t('error', {message: error})}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filter */}
      {sources.length > 0 && (
        <div className="flex items-center gap-3">
          <label
            htmlFor="source-filter"
            className="text-sm font-medium text-muted-foreground"
          >
            {t('filter')}
          </label>
          <select
            id="source-filter"
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary"
          >
            <option value="all">{t('allProvinces')}</option>
            {sources.map((source) => (
              <option key={source.id} value={source.id}>
                {source.province}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Timeline */}
      {events.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <svg
            className="w-12 h-12 mx-auto mb-3 text-muted-foreground/40"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="font-medium">{t('noEvents.title')}</p>
          <p className="text-sm mt-1">
            {t('noEvents.description')}
          </p>
        </div>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border"></div>

          {/* Events */}
          <div className="space-y-8">
            {events.map((event, index) => (
              <div key={event.id} className="relative pl-20">
                {/* Timeline dot */}
                <div className="absolute left-6 top-2 w-4 h-4 rounded-full bg-primary border-4 border-card shadow"></div>

                {/* Event card */}
                <div className="bg-card rounded-lg border border-border p-6 shadow-sm hover:shadow-md transition-shadow">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h4 className="font-semibold text-foreground text-lg">
                        {getSourceName(event.source_id)}
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        {t('detected', {date: formatDate(event.detected_at)})}
                      </p>
                    </div>
                    <div
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        Math.abs(event.shift_percent) >= 20
                          ? "bg-danger/10 text-danger"
                          : Math.abs(event.shift_percent) >= 10
                            ? "bg-warning/10 text-warning"
                            : "bg-primary/10 text-primary"
                      }`}
                    >
                      {event.shift_percent > 0 ? "+" : ""}
                      {event.shift_percent.toFixed(1)}%
                    </div>
                  </div>

                  {/* Explanation */}
                  <p className="text-muted-foreground mb-4">{event.explanation}</p>

                  {/* Details */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/50">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">
                        {t('previousPeriod')}
                      </p>
                      <p className="text-sm font-medium text-foreground">
                        {event.previous_period.mean.toFixed(0)} min
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatDate(event.previous_period.start)} -{" "}
                        {formatDate(event.previous_period.end)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">
                        {t('currentPeriod')}
                      </p>
                      <p className="text-sm font-medium text-foreground">
                        {event.current_period.mean.toFixed(0)} min
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatDate(event.current_period.start)} -{" "}
                        {formatDate(event.current_period.end)}
                      </p>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="mt-4 pt-4 border-t border-border/50 text-xs text-muted-foreground">
                    {event.hospitals_analyzed !== 1 ? t('analyzedPlural', {count: event.hospitals_analyzed}) : t('analyzed', {count: event.hospitals_analyzed})}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
