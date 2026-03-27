import { clsx } from "clsx";
import { useTranslations } from "next-intl";

import type { ResourceRecord } from "@/utils/public-health-hub";

interface ResourceListProps {
  resources: ResourceRecord[];
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

export function ResourceList({
  resources,
  loading = false,
  emptyTitle,
}: ResourceListProps) {
  const t = useTranslations("ResourceList");

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            key={index}
            className="h-32 animate-pulse rounded-2xl border border-border bg-card/50"
          />
        ))}
      </div>
    );
  }

  if (resources.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-card/40 p-8 text-center">
        <p className="text-sm font-medium text-foreground">
          {emptyTitle ?? t("emptyTitle")}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {resources.map((resource) => {
        const timestamp = formatTimestamp(resource.last_refreshed_at);
        const isWarn = resource.freshness_state === "warn";

        return (
          <article
            key={resource.id}
            className="rounded-2xl border border-border bg-card/80 p-5 shadow-sm"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-semibold text-foreground">
                    {resource.name}
                  </h3>
                  {resource.crowdsourced && (
                    <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
                      {t("labels.crowdsourced")}
                    </span>
                  )}
                  {resource.completeness_status === "incomplete" && (
                    <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                      {t("labels.incompleteCoverage")}
                    </span>
                  )}
                  {resource.location_description && (
                    <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary">
                      {resource.location_description}
                    </span>
                  )}
                  {resource.distance_km !== undefined && (
                    <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                      {t("distance", { distance: resource.distance_km })}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {[resource.city, resource.province]
                    .filter(Boolean)
                    .join(", ")}
                </p>
                {resource.address && (
                  <p className="mt-2 text-sm text-foreground">
                    {resource.address}
                  </p>
                )}
              </div>

              <div className="flex flex-col items-start gap-2 text-xs sm:items-end">
                <span
                  className={clsx(
                    "rounded-full px-2.5 py-1 font-medium",
                    isWarn
                      ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200"
                      : "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200",
                  )}
                >
                  {resource.freshness_state === "warn"
                    ? t("freshnessWarn")
                    : t("freshnessShow")}
                </span>
                {timestamp && (
                  <span className="text-muted-foreground">
                    {t("updatedAt", { timestamp })}
                  </span>
                )}
              </div>
            </div>

            <div className="mt-4 grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
              <div className="space-y-1">
                <p>
                  {resource.caveat_class === "reference_directory"
                    ? t("caveat.referenceDirectory")
                    : t("caveat.crowdsourcedIncomplete")}
                </p>
                <p>{t("sourceLabel", { source: resource.source_name })}</p>
              </div>
              <div className="space-y-1">
                {resource.phone && (
                  <p>{t("phoneLabel", { phone: resource.phone })}</p>
                )}
                {resource.website_url && (
                  <a
                    href={resource.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex text-primary hover:text-primary/80"
                  >
                    {t("websiteLink")}
                  </a>
                )}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
