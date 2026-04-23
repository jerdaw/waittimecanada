"use client";

import { useEffect, useMemo, useState } from "react";
import { clsx } from "clsx";
import { useTranslations } from "next-intl";

import { AlertFeed } from "@/components/AlertFeed";
import { AQHICard } from "@/components/AQHICard";
import { Header } from "@/components/Header";
import { ResourceList } from "@/components/ResourceList";
import type {
  AlertRecord,
  AQHIRecord,
  FreshnessState,
  ResourceRecord,
  SourceCatalogRecord,
  SourceStatusRecord,
  SystemContextDispatchCentreRecord,
  SystemContextParamedicServiceRecord,
} from "@/utils/public-health-hub";

interface ResourcesResponse {
  success: boolean;
  count: number;
  data: ResourceRecord[];
  meta: {
    scope?: {
      mode: "ontario_only";
      available_provinces: ["ON"];
      requested_province: string | null;
      note: string;
    };
    source_status: SourceStatusRecord[];
    source_catalog: SourceCatalogRecord[];
  };
}

interface AlertsResponse {
  success: boolean;
  count: number;
  data: AlertRecord[];
  meta: {
    source_status: SourceStatusRecord[];
    source_catalog: SourceCatalogRecord[];
  };
}

interface AQHIResponse {
  success: boolean;
  data: AQHIRecord | null;
  meta: {
    source_status: SourceStatusRecord[];
    source_catalog: SourceCatalogRecord[];
  };
}

interface SystemContextResponse {
  success: boolean;
  data: {
    dispatch_centres: SystemContextDispatchCentreRecord[];
    paramedic_services: SystemContextParamedicServiceRecord[];
  };
  meta: {
    source_status: SourceStatusRecord[];
    source_catalog: SourceCatalogRecord[];
  };
}

type TranslationFn = ReturnType<typeof useTranslations>;

function formatTimestamp(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  return new Date(value).toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatSourceCatalogEnum(
  t: TranslationFn,
  group:
    | "connectorType"
    | "licenseReuseStatus"
    | "recommendedUsageMode"
    | "updateCadence",
  value: string,
) {
  const translationKey = `sections.transparency.values.${group}.${value}`;
  const translated = t.raw(translationKey);

  if (typeof translated === "string" && translated !== translationKey) {
    return translated;
  }

  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatCompactNumber(
  value: number | null | undefined,
  options?: Intl.NumberFormatOptions,
) {
  if (value === null || value === undefined) {
    return null;
  }

  return formatPresentNumber(value, options);
}

function formatPresentNumber(
  value: number,
  options?: Intl.NumberFormatOptions,
) {
  return new Intl.NumberFormat(undefined, options).format(value);
}

function getFreshnessBadgeClasses(freshnessState: FreshnessState) {
  return clsx(
    "rounded-full px-2.5 py-1 text-[11px] font-medium",
    freshnessState === "show" &&
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200",
    freshnessState === "warn" &&
      "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200",
    freshnessState === "suppress" &&
      "bg-muted text-muted-foreground",
  );
}

function getFreshnessPriority(freshnessState: FreshnessState) {
  switch (freshnessState) {
    case "show":
      return 0;
    case "warn":
      return 1;
    case "suppress":
    default:
      return 2;
  }
}

function dedupeSourceCatalogRecords(records: SourceCatalogRecord[]) {
  const deduped = new Map<string, SourceCatalogRecord>();

  for (const record of records) {
    const existing = deduped.get(record.source_id);
    if (!existing) {
      deduped.set(record.source_id, record);
      continue;
    }

    const existingPriority = getFreshnessPriority(existing.freshness_state);
    const nextPriority = getFreshnessPriority(record.freshness_state);
    if (
      nextPriority < existingPriority ||
      (nextPriority === existingPriority &&
        record.last_refreshed_at &&
        !existing.last_refreshed_at)
    ) {
      deduped.set(record.source_id, record);
    }
  }

  return Array.from(deduped.values()).sort((left, right) =>
    left.source_name.localeCompare(right.source_name),
  );
}

export default function ResourcesPage() {
  const t = useTranslations("ResourcesPage");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
  const [resources, setResources] = useState<ResourceRecord[]>([]);
  const [resourcesLoading, setResourcesLoading] = useState(true);
  const [aedResources, setAEDResources] = useState<ResourceRecord[]>([]);
  const [aedLoading, setAEDLoading] = useState(true);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [aqhi, setAQHI] = useState<AQHIRecord | null>(null);
  const [aqhiLoading, setAQHILoading] = useState(false);
  const [dispatchCentres, setDispatchCentres] = useState<
    SystemContextDispatchCentreRecord[]
  >([]);
  const [paramedicServices, setParamedicServices] = useState<
    SystemContextParamedicServiceRecord[]
  >([]);
  const [systemContextLoading, setSystemContextLoading] = useState(true);
  const [userLocation, setUserLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [facilitySourceCatalog, setFacilitySourceCatalog] = useState<
    SourceCatalogRecord[]
  >([]);
  const [aedSourceCatalog, setAEDSourceCatalog] = useState<
    SourceCatalogRecord[]
  >([]);
  const [alertSourceCatalog, setAlertSourceCatalog] = useState<
    SourceCatalogRecord[]
  >([]);
  const [aqhiSourceStatus, setAQHISourceStatus] = useState<
    SourceStatusRecord[]
  >([]);
  const [aqhiSourceCatalog, setAQHISourceCatalog] = useState<
    SourceCatalogRecord[]
  >([]);
  const [systemContextSourceCatalog, setSystemContextSourceCatalog] = useState<
    SourceCatalogRecord[]
  >([]);
  const province = "ON";
  const facilityDiscoveryReady = Boolean(
    userLocation || debouncedSearchQuery.trim(),
  );

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedSearchQuery(searchQuery.trim());
    }, 250);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [searchQuery]);

  useEffect(() => {
    let mounted = true;

    async function loadResources() {
      if (!facilityDiscoveryReady) {
        setResources([]);
        setFacilitySourceCatalog([]);
        setResourcesLoading(false);
        return;
      }

      setResourcesLoading(true);
      try {
        const params = new URLSearchParams({
          kind: "facility",
          province,
          limit: "20",
        });

        if (debouncedSearchQuery) {
          params.set("q", debouncedSearchQuery);
        }

        if (userLocation) {
          params.set("latitude", String(userLocation.latitude));
          params.set("longitude", String(userLocation.longitude));
          params.set("radius", "50");
        }

        const response = await fetch(`/api/resources?${params.toString()}`);
        const payload = (await response.json()) as ResourcesResponse;

        if (!mounted) return;

        if (response.ok && payload.success) {
          setResources(payload.data);
          setFacilitySourceCatalog(payload.meta.source_catalog ?? []);
        } else {
          setResources([]);
          setFacilitySourceCatalog([]);
        }
      } catch {
        if (!mounted) return;
        setResources([]);
        setFacilitySourceCatalog([]);
      } finally {
        if (mounted) {
          setResourcesLoading(false);
        }
      }
    }

    loadResources();
    return () => {
      mounted = false;
    };
  }, [debouncedSearchQuery, facilityDiscoveryReady, userLocation]);

  useEffect(() => {
    let mounted = true;

    async function loadAEDResources() {
      setAEDLoading(true);
      try {
        const params = new URLSearchParams({
          kind: "aed",
          province,
          limit: "12",
        });

        if (debouncedSearchQuery) {
          params.set("q", debouncedSearchQuery);
        }

        if (userLocation) {
          params.set("latitude", String(userLocation.latitude));
          params.set("longitude", String(userLocation.longitude));
          params.set("radius", "25");
        }

        const response = await fetch(`/api/resources?${params.toString()}`);
        const payload = (await response.json()) as ResourcesResponse;

        if (!mounted) return;

        if (response.ok && payload.success) {
          setAEDResources(payload.data);
          setAEDSourceCatalog(payload.meta.source_catalog ?? []);
        } else {
          setAEDResources([]);
          setAEDSourceCatalog([]);
        }
      } catch {
        if (!mounted) return;
        setAEDResources([]);
        setAEDSourceCatalog([]);
      } finally {
        if (mounted) {
          setAEDLoading(false);
        }
      }
    }

    loadAEDResources();
    return () => {
      mounted = false;
    };
  }, [debouncedSearchQuery, userLocation]);

  useEffect(() => {
    let mounted = true;

    async function loadAlerts() {
      setAlertsLoading(true);
      try {
        const response = await fetch("/api/resources/alerts?limit=10");
        const payload = (await response.json()) as AlertsResponse;

        if (!mounted) return;

        if (response.ok && payload.success) {
          setAlerts(payload.data);
          setAlertSourceCatalog(payload.meta.source_catalog ?? []);
        } else {
          setAlerts([]);
          setAlertSourceCatalog([]);
        }
      } catch {
        if (!mounted) return;
        setAlerts([]);
        setAlertSourceCatalog([]);
      } finally {
        if (mounted) {
          setAlertsLoading(false);
        }
      }
    }

    loadAlerts();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadAQHI() {
      if (!userLocation) {
        setAQHI(null);
        setAQHISourceStatus([]);
        setAQHISourceCatalog([]);
        return;
      }

      setAQHILoading(true);
      try {
        const params = new URLSearchParams({
          latitude: String(userLocation.latitude),
          longitude: String(userLocation.longitude),
        });
        const response = await fetch(
          `/api/resources/aqhi?${params.toString()}`,
        );
        const payload = (await response.json()) as AQHIResponse;

        if (!mounted) return;

        if (response.ok && payload.success) {
          setAQHI(payload.data);
          setAQHISourceStatus(payload.meta.source_status ?? []);
          setAQHISourceCatalog(payload.meta.source_catalog ?? []);
        } else {
          setAQHI(null);
          setAQHISourceStatus([]);
          setAQHISourceCatalog([]);
        }
      } catch {
        if (!mounted) return;
        setAQHI(null);
        setAQHISourceStatus([]);
        setAQHISourceCatalog([]);
      } finally {
        if (mounted) {
          setAQHILoading(false);
        }
      }
    }

    loadAQHI();
    return () => {
      mounted = false;
    };
  }, [userLocation]);

  useEffect(() => {
    let mounted = true;

    async function loadSystemContext() {
      setSystemContextLoading(true);
      try {
        const params = new URLSearchParams({
          province,
          limit: "8",
        });

        if (debouncedSearchQuery) {
          params.set("q", debouncedSearchQuery);
        }

        const response = await fetch(
          `/api/resources/system-context?${params.toString()}`,
        );
        const payload = (await response.json()) as SystemContextResponse;

        if (!mounted) return;

        if (response.ok && payload.success) {
          setDispatchCentres(payload.data.dispatch_centres);
          setParamedicServices(payload.data.paramedic_services);
          setSystemContextSourceCatalog(payload.meta.source_catalog ?? []);
        } else {
          setDispatchCentres([]);
          setParamedicServices([]);
          setSystemContextSourceCatalog([]);
        }
      } catch {
        if (!mounted) return;
        setDispatchCentres([]);
        setParamedicServices([]);
        setSystemContextSourceCatalog([]);
      } finally {
        if (mounted) {
          setSystemContextLoading(false);
        }
      }
    }

    loadSystemContext();
    return () => {
      mounted = false;
    };
  }, [debouncedSearchQuery]);

  const sourceCatalog = useMemo(() => {
    const entries = [
      ...facilitySourceCatalog,
      ...aedSourceCatalog,
      ...alertSourceCatalog,
      ...aqhiSourceCatalog,
      ...systemContextSourceCatalog,
    ];
    return dedupeSourceCatalogRecords(entries);
  }, [
    facilitySourceCatalog,
    aedSourceCatalog,
    alertSourceCatalog,
    aqhiSourceCatalog,
    systemContextSourceCatalog,
  ]);
  const systemContextSource = systemContextSourceCatalog[0] ?? null;
  const systemContextSuppressed =
    systemContextSource?.freshness_state === "suppress";
  const systemContextMethodologyNote =
    systemContextSource?.public_methodology_note ??
    t("sections.systemContext.fallbackMethodology");

  const resourcesSectionTitle = userLocation
    ? t("sections.resources.nearbyTitle")
    : t("sections.resources.title");
  const resourcesSectionDescription = userLocation
    ? t("sections.resources.nearbyDescription")
    : t("sections.resources.description");
  const aedSectionTitle = userLocation
    ? t("sections.aed.nearbyTitle")
    : t("sections.aed.title");
  const aedSectionDescription = userLocation
    ? t("sections.aed.nearbyDescription")
    : t("sections.aed.description");

  const requestLocation = () => {
    if (!("geolocation" in navigator)) {
      setLocationError(t("filters.locationUnsupported"));
      return;
    }

    setLocationError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          setLocationError(t("filters.locationDenied"));
          return;
        }

        setLocationError(t("filters.locationError"));
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000,
      },
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-background">
      <Header />

      <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        <section className="rounded-3xl border border-border bg-card/80 p-6 shadow-sm">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-primary">
              {t("eyebrow")}
            </p>
            <h1 className="mt-3 text-3xl font-bold tracking-tight text-foreground">
              {t("title")}
            </h1>
            <p className="mt-3 text-base leading-7 text-muted-foreground">
              {t("description")}
            </p>
          </div>

          <div className="mt-6 grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
            <label className="flex flex-col gap-2">
              <span className="text-sm font-medium text-foreground">
                {t("filters.search")}
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder={t("filters.searchPlaceholder")}
                className="rounded-xl border border-border bg-background px-3 py-2 text-sm"
              />
            </label>

            <div className="flex items-end">
              <div className="w-full lg:w-auto">
                <button
                  type="button"
                  onClick={requestLocation}
                  className="w-full rounded-xl border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/15 lg:w-auto"
                >
                  {t("filters.useLocation")}
                </button>
                {locationError && (
                  <p className="mt-2 max-w-xs text-xs text-amber-700 dark:text-amber-300">
                    {locationError}
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
          <section className="space-y-4">
            <div>
              <h2 className="text-2xl font-semibold text-foreground">
                {resourcesSectionTitle}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {resourcesSectionDescription}
              </p>
            </div>
            <ResourceList
              resources={resources}
              loading={resourcesLoading}
              emptyTitle={
                facilityDiscoveryReady
                  ? t("sections.resources.empty")
                  : t("sections.resources.gated")
              }
            />
          </section>

          <section className="space-y-4">
            <div>
              <h2 className="text-2xl font-semibold text-foreground">
                {t("sections.transparency.title")}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {t("sections.transparency.description")}
              </p>
            </div>
            <div className="space-y-3">
              {sourceCatalog.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border bg-card/40 p-6 text-sm text-muted-foreground">
                  {t("sections.transparency.empty")}
                </div>
              ) : (
                sourceCatalog.map((source) => (
                  <article
                    key={source.source_id}
                    className="rounded-2xl border border-border bg-card/80 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-medium text-foreground">
                          {source.source_name}
                        </h3>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {t("sections.transparency.lastRefreshed", {
                            timestamp:
                              formatTimestamp(source.last_refreshed_at) ??
                              t("common.unknown"),
                          })}
                        </p>
                      </div>
                      <span
                        className={getFreshnessBadgeClasses(
                          source.freshness_state,
                        )}
                      >
                        {t(
                          `sections.transparency.freshness.${source.freshness_state}`,
                        )}
                      </span>
                    </div>
                    <dl className="mt-4 grid gap-3 text-xs text-muted-foreground sm:grid-cols-2">
                      <div className="space-y-1">
                        <dt className="font-medium text-foreground">
                          {t("sections.transparency.fields.lastVerified")}
                        </dt>
                        <dd>
                          {formatTimestamp(source.last_verified_at) ??
                            t("common.unknown")}
                        </dd>
                      </div>
                      <div className="space-y-1">
                        <dt className="font-medium text-foreground">
                          {t("sections.transparency.fields.connectorType")}
                        </dt>
                        <dd>
                          {formatSourceCatalogEnum(
                            t,
                            "connectorType",
                            source.connector_type,
                          )}
                        </dd>
                      </div>
                      <div className="space-y-1">
                        <dt className="font-medium text-foreground">
                          {t("sections.transparency.fields.accessRoute")}
                        </dt>
                        <dd>{source.access_route}</dd>
                      </div>
                      <div className="space-y-1">
                        <dt className="font-medium text-foreground">
                          {t("sections.transparency.fields.reusePosture")}
                        </dt>
                        <dd>
                          {formatSourceCatalogEnum(
                            t,
                            "licenseReuseStatus",
                            source.license_reuse_status,
                          )}
                        </dd>
                      </div>
                      <div className="space-y-1">
                        <dt className="font-medium text-foreground">
                          {t("sections.transparency.fields.attribution")}
                        </dt>
                        <dd>{source.attribution_requirement}</dd>
                      </div>
                      <div className="space-y-1">
                        <dt className="font-medium text-foreground">
                          {t("sections.transparency.fields.updateCadence")}
                        </dt>
                        <dd>
                          {formatSourceCatalogEnum(
                            t,
                            "updateCadence",
                            source.update_cadence,
                          )}
                        </dd>
                      </div>
                      <div className="space-y-1">
                        <dt className="font-medium text-foreground">
                          {t("sections.transparency.fields.usageMode")}
                        </dt>
                        <dd>
                          {formatSourceCatalogEnum(
                            t,
                            "recommendedUsageMode",
                            source.recommended_usage_mode,
                          )}
                        </dd>
                      </div>
                    </dl>
                    {source.public_methodology_note && (
                      <div className="mt-4 rounded-xl border border-primary/10 bg-primary/5 p-3 text-xs leading-6 text-foreground">
                        <p className="font-medium">
                          {t("sections.transparency.fields.methodologyNote")}
                        </p>
                        <p className="mt-1 text-muted-foreground">
                          {source.public_methodology_note}
                        </p>
                      </div>
                    )}
                    <a
                      href={source.provenance_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-flex text-sm text-primary hover:text-primary/80"
                    >
                      {t("sections.transparency.sourceLink")}
                    </a>
                  </article>
                ))
              )}
            </div>
          </section>
        </div>

        <section className="grid gap-8 lg:grid-cols-2">
          <div className="rounded-3xl border border-border bg-card/80 p-6 shadow-sm">
            <h2 className="text-2xl font-semibold text-foreground">
              {aedSectionTitle}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {aedSectionDescription}
            </p>
            <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/80 p-4 text-sm text-amber-950">
              <p className="font-medium">{t("sections.aed.caveatTitle")}</p>
              <p className="mt-1 text-amber-900">
                {t("sections.aed.caveat")}
              </p>
            </div>
            <div className="mt-4">
              <ResourceList
                resources={aedResources}
                loading={aedLoading}
                emptyTitle={t("sections.aed.empty")}
              />
            </div>
          </div>

          <div className="rounded-3xl border border-border bg-card/80 p-6 shadow-sm">
            <h2 className="text-2xl font-semibold text-foreground">
              {t("sections.alerts.title")}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("sections.alerts.description")}
            </p>
            <div className="mt-4">
              <AlertFeed
                alerts={alerts}
                loading={alertsLoading}
                emptyTitle={t("sections.alerts.empty")}
              />
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-border bg-card/80 p-6 shadow-sm">
          <div className="max-w-3xl">
            <h2 className="text-2xl font-semibold text-foreground">
              {t("sections.systemContext.title")}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("sections.systemContext.description")}
            </p>
          </div>

          <div className="mt-4 rounded-2xl border border-sky-200 bg-sky-50/80 p-4 text-sm text-sky-950">
            <p className="text-xs font-semibold uppercase tracking-[0.16em]">
              {t("sections.systemContext.methodologyLabel")}
            </p>
            <p className="mt-2 leading-6">{systemContextMethodologyNote}</p>
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-2">
            <article className="rounded-2xl border border-border bg-background p-5">
              <h3 className="text-lg font-semibold text-foreground">
                {t("sections.systemContext.dispatchCentres.title")}
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {t("sections.systemContext.dispatchCentres.description")}
              </p>
              <div className="mt-4">
                {systemContextLoading ? (
                  <div className="rounded-2xl border border-dashed border-border bg-card/40 p-4 text-sm text-muted-foreground">
                    {t("sections.systemContext.loading")}
                  </div>
                ) : systemContextSuppressed ? (
                  <div className="rounded-2xl border border-dashed border-border bg-card/40 p-4 text-sm text-muted-foreground">
                    {t("sections.systemContext.suppressed")}
                  </div>
                ) : dispatchCentres.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border bg-card/40 p-4 text-sm text-muted-foreground">
                    {t("sections.systemContext.dispatchCentres.empty")}
                  </div>
                ) : (
                  <ul className="space-y-3">
                    {dispatchCentres.map((centre) => (
                      <li
                        key={centre.id}
                        className="rounded-2xl border border-border bg-card/80 p-4"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h4 className="font-medium text-foreground">
                              {centre.geography_name}
                            </h4>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {t("sections.systemContext.reportingYear", {
                                year: centre.reporting_year,
                              })}
                            </p>
                          </div>
                        </div>
                        <dl className="mt-4 grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
                          <div className="space-y-1">
                            <dt className="font-medium text-foreground">
                              {t(
                                "sections.systemContext.dispatchCentres.averageResponseTime",
                              )}
                            </dt>
                            <dd>
                              {centre.average_response_time_minutes !== null
                                ? t(
                                    "sections.systemContext.dispatchCentres.averageResponseTimeValue",
                                    {
                                      value: formatPresentNumber(
                                        centre.average_response_time_minutes,
                                        {
                                          maximumFractionDigits: 1,
                                        },
                                      ),
                                    },
                                  )
                                : t("sections.systemContext.notReported")}
                            </dd>
                          </div>
                          <div className="space-y-1">
                            <dt className="font-medium text-foreground">
                              {t("sections.systemContext.dispatchCentres.callVolume")}
                            </dt>
                            <dd>
                              {centre.call_volume !== null
                                ? formatCompactNumber(centre.call_volume)
                                : t("sections.systemContext.notReported")}
                            </dd>
                          </div>
                        </dl>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </article>

            <article className="rounded-2xl border border-border bg-background p-5">
              <h3 className="text-lg font-semibold text-foreground">
                {t("sections.systemContext.paramedicServices.title")}
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {t("sections.systemContext.paramedicServices.description")}
              </p>
              <div className="mt-4">
                {systemContextLoading ? (
                  <div className="rounded-2xl border border-dashed border-border bg-card/40 p-4 text-sm text-muted-foreground">
                    {t("sections.systemContext.loading")}
                  </div>
                ) : systemContextSuppressed ? (
                  <div className="rounded-2xl border border-dashed border-border bg-card/40 p-4 text-sm text-muted-foreground">
                    {t("sections.systemContext.suppressed")}
                  </div>
                ) : paramedicServices.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border bg-card/40 p-4 text-sm text-muted-foreground">
                    {t("sections.systemContext.paramedicServices.empty")}
                  </div>
                ) : (
                  <ul className="space-y-3">
                    {paramedicServices.map((service) => (
                      <li
                        key={service.id}
                        className="rounded-2xl border border-border bg-card/80 p-4"
                      >
                        <div>
                          <h4 className="font-medium text-foreground">
                            {service.geography_name}
                          </h4>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {t("sections.systemContext.reportingYear", {
                              year: service.reporting_year,
                            })}
                          </p>
                        </div>
                        <ul className="mt-4 space-y-3">
                          {service.severity_breakdown.map((severity, index) => (
                            <li
                              key={`${service.id}-${severity.patient_severity ?? "na"}-${index}`}
                              className="rounded-xl border border-border/70 bg-background p-3"
                            >
                              <p className="text-sm font-medium text-foreground">
                                {severity.patient_severity ??
                                  t("sections.systemContext.notReported")}
                              </p>
                              <dl className="mt-3 grid gap-3 text-xs text-muted-foreground sm:grid-cols-3">
                                <div className="space-y-1">
                                  <dt className="font-medium text-foreground">
                                    {t(
                                      "sections.systemContext.paramedicServices.responsePlan",
                                    )}
                                  </dt>
                                  <dd>
                                    {severity.response_time_plan_minutes !== null
                                      ? t(
                                          "sections.systemContext.paramedicServices.minutesValue",
                                          {
                                            value: formatPresentNumber(
                                              severity.response_time_plan_minutes,
                                              {
                                                maximumFractionDigits: 1,
                                              },
                                            ),
                                          },
                                        )
                                      : t("sections.systemContext.notReported")}
                                  </dd>
                                </div>
                                <div className="space-y-1">
                                  <dt className="font-medium text-foreground">
                                    {t(
                                      "sections.systemContext.paramedicServices.plannedResponse",
                                    )}
                                  </dt>
                                  <dd>
                                    {severity.planned_response_pct !== null
                                      ? t(
                                          "sections.systemContext.paramedicServices.percentValue",
                                          {
                                            value: formatPresentNumber(
                                              severity.planned_response_pct,
                                              {
                                                maximumFractionDigits: 1,
                                              },
                                            ),
                                          },
                                        )
                                      : t("sections.systemContext.notReported")}
                                  </dd>
                                </div>
                                <div className="space-y-1">
                                  <dt className="font-medium text-foreground">
                                    {t(
                                      "sections.systemContext.paramedicServices.performance",
                                    )}
                                  </dt>
                                  <dd>
                                    {severity.performance_pct !== null
                                      ? t(
                                          "sections.systemContext.paramedicServices.percentValue",
                                          {
                                            value: formatPresentNumber(
                                              severity.performance_pct,
                                              {
                                                maximumFractionDigits: 1,
                                              },
                                            ),
                                          },
                                        )
                                      : t("sections.systemContext.notReported")}
                                  </dd>
                                </div>
                              </dl>
                            </li>
                          ))}
                        </ul>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </article>
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-1">
          <div className="rounded-3xl border border-border bg-card/80 p-6 shadow-sm">
            <h2 className="text-2xl font-semibold text-foreground">
              {t("sections.naloxone.title")}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("sections.naloxone.description")}
            </p>
            <div className="mt-4 rounded-2xl border border-border bg-background p-4">
              <p className="text-sm text-foreground">
                {t("sections.naloxone.caveat")}
              </p>
              <a
                href="https://www.ontario.ca/page/where-get-free-naloxone-kit"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-flex rounded-xl border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/15"
              >
                {t("sections.naloxone.link")}
              </a>
            </div>
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-1">
          <div className="rounded-3xl border border-border bg-card/80 p-6 shadow-sm">
            <h2 className="text-2xl font-semibold text-foreground">
              {t("sections.aqhi.title")}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("sections.aqhi.description")}
            </p>
            <div className="mt-4 rounded-2xl border border-border bg-background p-4">
              <AQHICard
                aqhi={aqhi}
                loading={aqhiLoading}
                requiresLocation={!userLocation}
                sourceStatus={aqhiSourceStatus[0] ?? null}
              />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
