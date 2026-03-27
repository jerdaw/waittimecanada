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
  ResourceRecord,
  SourceStatusRecord,
} from "@/utils/public-health-hub";

interface ResourcesResponse {
  success: boolean;
  count: number;
  data: ResourceRecord[];
  meta: {
    source_status: SourceStatusRecord[];
  };
}

interface AlertsResponse {
  success: boolean;
  count: number;
  data: AlertRecord[];
  meta: {
    source_status: SourceStatusRecord[];
  };
}

interface AQHIResponse {
  success: boolean;
  data: AQHIRecord | null;
  meta: {
    source_status: SourceStatusRecord[];
  };
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

export default function ResourcesPage() {
  const t = useTranslations("ResourcesPage");
  const [province, setProvince] = useState("ON");
  const [searchQuery, setSearchQuery] = useState("");
  const [resources, setResources] = useState<ResourceRecord[]>([]);
  const [resourcesLoading, setResourcesLoading] = useState(true);
  const [aedResources, setAEDResources] = useState<ResourceRecord[]>([]);
  const [aedLoading, setAEDLoading] = useState(true);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [aqhi, setAQHI] = useState<AQHIRecord | null>(null);
  const [aqhiLoading, setAQHILoading] = useState(false);
  const [userLocation, setUserLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [facilitySourceStatus, setFacilitySourceStatus] = useState<
    SourceStatusRecord[]
  >([]);
  const [aedSourceStatus, setAEDSourceStatus] = useState<SourceStatusRecord[]>(
    [],
  );
  const [alertSourceStatus, setAlertSourceStatus] = useState<
    SourceStatusRecord[]
  >([]);
  const [aqhiSourceStatus, setAQHISourceStatus] = useState<
    SourceStatusRecord[]
  >([]);

  useEffect(() => {
    let mounted = true;

    async function loadResources() {
      setResourcesLoading(true);
      try {
        const params = new URLSearchParams({
          kind: "facility",
          province,
          limit: "20",
        });

        if (searchQuery.trim()) {
          params.set("q", searchQuery.trim());
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
          setFacilitySourceStatus(payload.meta.source_status ?? []);
        } else {
          setResources([]);
          setFacilitySourceStatus([]);
        }
      } catch {
        if (!mounted) return;
        setResources([]);
        setFacilitySourceStatus([]);
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
  }, [province, searchQuery, userLocation]);

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

        if (searchQuery.trim()) {
          params.set("q", searchQuery.trim());
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
          setAEDSourceStatus(payload.meta.source_status ?? []);
        } else {
          setAEDResources([]);
          setAEDSourceStatus([]);
        }
      } catch {
        if (!mounted) return;
        setAEDResources([]);
        setAEDSourceStatus([]);
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
  }, [province, searchQuery, userLocation]);

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
          setAlertSourceStatus(payload.meta.source_status ?? []);
        } else {
          setAlerts([]);
          setAlertSourceStatus([]);
        }
      } catch {
        if (!mounted) return;
        setAlerts([]);
        setAlertSourceStatus([]);
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
        } else {
          setAQHI(null);
          setAQHISourceStatus([]);
        }
      } catch {
        if (!mounted) return;
        setAQHI(null);
        setAQHISourceStatus([]);
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

  const sourceStatus = useMemo(() => {
    const entries = [
      ...facilitySourceStatus,
      ...aedSourceStatus,
      ...alertSourceStatus,
      ...aqhiSourceStatus,
    ];
    const deduped = new Map<string, SourceStatusRecord>();
    for (const entry of entries) {
      deduped.set(entry.source_id, entry);
    }
    return Array.from(deduped.values());
  }, [
    facilitySourceStatus,
    aedSourceStatus,
    alertSourceStatus,
    aqhiSourceStatus,
  ]);

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

          <div className="mt-6 grid gap-3 lg:grid-cols-[180px_minmax(0,1fr)_auto]">
            <label className="flex flex-col gap-2">
              <span className="text-sm font-medium text-foreground">
                {t("filters.province")}
              </span>
              <select
                value={province}
                onChange={(event) => setProvince(event.target.value)}
                className="rounded-xl border border-border bg-background px-3 py-2 text-sm"
              >
                <option value="ON">Ontario</option>
                <option value="QC">Quebec</option>
                <option value="AB">Alberta</option>
                <option value="BC">British Columbia</option>
              </select>
            </label>

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
                {t("sections.resources.title")}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {t("sections.resources.description")}
              </p>
            </div>
            <ResourceList
              resources={resources}
              loading={resourcesLoading}
              emptyTitle={t("sections.resources.empty")}
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
              {sourceStatus.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border bg-card/40 p-6 text-sm text-muted-foreground">
                  {t("sections.transparency.empty")}
                </div>
              ) : (
                sourceStatus.map((source) => (
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
                          {t("sections.transparency.updated", {
                            timestamp:
                              formatTimestamp(source.last_refreshed_at) ??
                              t("common.unknown"),
                          })}
                        </p>
                      </div>
                      <span
                        className={clsx(
                          "rounded-full px-2.5 py-1 text-[11px] font-medium",
                          source.freshness_state === "show" &&
                            "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200",
                          source.freshness_state === "warn" &&
                            "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200",
                          source.freshness_state === "suppress" &&
                            "bg-muted text-muted-foreground",
                        )}
                      >
                        {t(
                          `sections.transparency.freshness.${source.freshness_state}`,
                        )}
                      </span>
                    </div>
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
              {t("sections.aed.title")}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("sections.aed.description")}
            </p>
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
