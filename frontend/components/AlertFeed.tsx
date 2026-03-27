import { useTranslations } from "next-intl";

import type { AlertRecord } from "@/utils/public-health-hub";

interface AlertFeedProps {
  alerts: AlertRecord[];
  loading?: boolean;
  emptyTitle?: string;
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  return new Date(value).toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function AlertFeed({
  alerts,
  loading = false,
  emptyTitle,
}: AlertFeedProps) {
  const t = useTranslations("AlertFeed");

  if (loading) {
    return (
      <div className="rounded-2xl border border-border bg-card/50 p-6 text-sm text-muted-foreground">
        {t("loading")}
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-card/40 p-6 text-sm text-muted-foreground">
        {emptyTitle ?? t("empty")}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <article
          key={alert.id}
          className="rounded-2xl border border-border bg-background p-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="font-medium text-foreground">{alert.title}</h3>
            <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
              {alert.alert_type}
            </span>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{alert.summary}</p>
          <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
            <span>{t("source", { source: alert.source_name })}</span>
            <span>
              {t("published", {
                timestamp: formatTimestamp(alert.published_at) ?? alert.published_at,
              })}
            </span>
            {alert.last_refreshed_at && (
              <span>
                {t("refreshed", {
                  timestamp:
                    formatTimestamp(alert.last_refreshed_at) ??
                    alert.last_refreshed_at,
                })}
              </span>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
