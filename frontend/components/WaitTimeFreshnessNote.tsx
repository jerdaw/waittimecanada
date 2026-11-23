import { useLocale, useTranslations } from "next-intl";
import {
  ONTARIO_HEALTH_SOURCE_URL,
  getMonthlySourceUrl,
  type WaitTimeStatus,
} from "@/utils/wait-time-freshness";

export function formatReportDate(
  value: string | undefined | null,
  locale: string,
): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

interface WaitTimeFreshnessNoteProps {
  status: WaitTimeStatus | undefined;
  lastUpdated: string | undefined | null;
  sourceId?: string;
  /**
   * Show the longer explanation and the source link (expanded views). The
   * short form has no link so it can sit inside a button.
   */
  detailed?: boolean;
  className?: string;
}

/**
 * Explains a wait-time value that is not current: either a live-estimate value
 * that has gone stale ("No current data" plus the last report date) or a
 * monthly average (Ontario Health). Renders nothing for current values.
 */
export function WaitTimeFreshnessNote({
  status,
  lastUpdated,
  sourceId = "ontario-health",
  detailed = false,
  className,
}: WaitTimeFreshnessNoteProps) {
  const t = useTranslations("WaitTimeFreshness");
  const locale = useLocale();
  const date = formatReportDate(lastUpdated, locale);

  if (status === "stale") {
    return (
      <span className={className} data-testid="wait-time-stale-note">
        <span className="font-medium">{t("noCurrentData")}</span>
        {date && <span className="block">{t("lastReported", { date })}</span>}
      </span>
    );
  }

  if (status === "monthly") {
    const sourceUrl =
      getMonthlySourceUrl(sourceId) ?? ONTARIO_HEALTH_SOURCE_URL;
    return (
      <span className={className} data-testid="wait-time-monthly-note">
        <span className="font-medium">{t("monthlyAverage")}</span>
        {detailed && <span className="block">{t("monthlyNote")}</span>}
        {detailed && <span className="block">{t("monthlyPeriodNote")}</span>}
        {date && <span className="block">{t("lastChecked", { date })}</span>}
        {detailed && <span className="block">{t("lastCheckedNote")}</span>}
        {detailed && (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="block underline"
          >
            {t("viewSource")}
          </a>
        )}
      </span>
    );
  }

  return null;
}
