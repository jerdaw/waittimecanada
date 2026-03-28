import { useTranslations } from "next-intl";

import type { AQHIRecord, SourceStatusRecord } from "@/utils/public-health-hub";

interface AQHICardProps {
  aqhi: AQHIRecord | null;
  loading?: boolean;
  requiresLocation?: boolean;
  sourceStatus?: SourceStatusRecord | null;
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

export function AQHICard({
  aqhi,
  loading = false,
  requiresLocation = false,
  sourceStatus = null,
}: AQHICardProps) {
  const t = useTranslations("AQHICard");

  if (requiresLocation) {
    return (
      <p className="text-sm text-muted-foreground">{t("locationPrompt")}</p>
    );
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">{t("loading")}</p>;
  }

  if (!aqhi) {
    return (
      <div className="space-y-2 text-sm text-muted-foreground">
        <p>
          {sourceStatus?.freshness_state === "suppress"
            ? t("suppressed")
            : t("empty")}
        </p>
        {sourceStatus?.last_refreshed_at && (
          <p className="text-xs">
            {t("refreshedAt", {
              timestamp:
                formatTimestamp(sourceStatus.last_refreshed_at) ??
                sourceStatus.last_refreshed_at,
            })}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-foreground">
        {aqhi.location_name}
      </p>
      <p className="text-3xl font-bold text-foreground">{aqhi.aqhi_value}</p>
      <p className="text-sm capitalize text-muted-foreground">
        {aqhi.category}
      </p>
      <p className="text-xs text-muted-foreground">
        {t("issuedAt", {
          timestamp: formatTimestamp(aqhi.issued_at) ?? aqhi.issued_at,
        })}
      </p>
      {aqhi.valid_until && (
        <p className="text-xs text-muted-foreground">
          {t("validUntil", {
            timestamp: formatTimestamp(aqhi.valid_until) ?? aqhi.valid_until,
          })}
        </p>
      )}
      <p className="text-xs text-muted-foreground">{t("caveat")}</p>
    </div>
  );
}
