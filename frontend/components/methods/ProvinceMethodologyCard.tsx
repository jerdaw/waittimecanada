import { useTranslations } from "next-intl";

interface Source {
  id: string;
  name: string;
  province: string;
  url: string;
  methodology_url: string | null;
  default_metric_family: string;
  default_start_event: string;
  default_end_event: string;
  default_statistic_type: string;
}

interface ProvinceMethodologyCardProps {
  source: Source;
}

export function ProvinceMethodologyCard({
  source,
}: ProvinceMethodologyCardProps) {
  const t = useTranslations('Methods.ProvinceMethodologyCard');

  return (
    <div
      className="rounded-xl border border-border bg-card p-6 transition-all duration-200 hover:shadow-lg"
    >
      {/* Header */}
      <div className="mb-4 pb-4 border-b border-border">
        <h3 className="text-xl font-bold text-primary mb-1">
          {source.province}
        </h3>
        <p className="text-sm text-muted-foreground">{source.name}</p>
      </div>

      {/* Methodology details */}
      <div className="space-y-4">
        <MethodologyField
          label="Metric Family"
          value={source.default_metric_family}
          description={t(`metricFamily.${source.default_metric_family}`)}
        />
        <MethodologyField
          label="Start Event"
          value={source.default_start_event}
          description={t(`startEvent.${source.default_start_event}`)}
        />
        <MethodologyField
          label="End Event"
          value={source.default_end_event}
          description={t(`endEvent.${source.default_end_event}`)}
        />
        <MethodologyField
          label="Statistic Type"
          value={source.default_statistic_type}
          description={t(`statisticType.${source.default_statistic_type}`)}
        />
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-border">
        {source.methodology_url ? (
          <a
            href={source.methodology_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
          >
            {t('viewOfficial')}
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
        ) : (
          <span className="text-sm text-muted-foreground">
            {t('notAvailable')}
          </span>
        )}
      </div>
    </div>
  );
}

function MethodologyField({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description?: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          {label}
        </span>
        <code className="px-2 py-1 rounded bg-muted text-xs font-mono text-foreground border border-border">
          {value}
        </code>
      </div>
      {description && (
        <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
      )}
    </div>
  );
}
