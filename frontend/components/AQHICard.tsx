import { useTranslations } from "next-intl";

import type { AQHIRecord } from "@/utils/public-health-hub";

interface AQHICardProps {
  aqhi: AQHIRecord | null;
  loading?: boolean;
  requiresLocation?: boolean;
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
}: AQHICardProps) {
  const t = useTranslations("AQHICard");

  if (requiresLocation) {
    return <p className="text-sm text-muted-foreground">{t("locationPrompt")}</p>;
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">{t("loading")}</p>;
  }

  if (!aqhi) {
    return <p className="text-sm text-muted-foreground">{t("empty")}</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-foreground">{aqhi.location_name}</p>
      <p className="text-3xl font-bold text-foreground">{aqhi.aqhi_value}</p>
      <p className="text-sm capitalize text-muted-foreground">{aqhi.category}</p>
      <p className="text-xs text-muted-foreground">
        {t("issuedAt", {
          timestamp: formatTimestamp(aqhi.issued_at) ?? aqhi.issued_at,
        })}
      </p>
      <p className="text-xs text-muted-foreground">{t("caveat")}</p>
    </div>
  );
}
