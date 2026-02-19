"use client";

import { useState, useEffect } from "react";
import { Activity, CheckCircle, AlertTriangle, XCircle } from "lucide-react";
import { useTranslations } from "next-intl";

type Status = "healthy" | "degraded" | "down" | "loading";

interface HealthData {
  status: Status;
  lastUpdate: string | null;
  ageMinutes: number;
  sourceCount: number;
  staleThresholdMinutes: number;
}

const HEALTH_CHECK_INTERVAL_MS = 5 * 60 * 1000;

export function SystemStatus() {
  const t = useTranslations('SystemStatus');
  const [health, setHealth] = useState<HealthData>({
    status: "loading",
    lastUpdate: null,
    ageMinutes: 0,
    sourceCount: 0,
    staleThresholdMinutes: 90,
  });

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch("/api/health");
        const data = await res.json();
        const staleThreshold = Number(data.stale_threshold_minutes ?? 90);

        // Calculate age from most recent update
        let ageMinutes = 999;
        if (data.last_update) {
          const lastUpdate = new Date(data.last_update);
          ageMinutes = Math.round((Date.now() - lastUpdate.getTime()) / 60000);
        }

        // Determine status based on overall health and age
        let status: Status = "healthy";
        if (!data.healthy || ageMinutes > staleThreshold * 2) {
          status = "down";
        } else if (ageMinutes > staleThreshold) {
          status = "degraded";
        }

        setHealth({
          status,
          lastUpdate: data.last_update,
          ageMinutes,
          sourceCount: data.sources?.length || 0,
          staleThresholdMinutes: staleThreshold,
        });
      } catch {
        setHealth({
          status: "down",
          lastUpdate: null,
          ageMinutes: 999,
          sourceCount: 0,
          staleThresholdMinutes: 90,
        });
      }
    }

    checkHealth();

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        checkHealth();
      }
    };

    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        checkHealth();
      }
    }, HEALTH_CHECK_INTERVAL_MS);

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, []);

  const statusConfig = {
    loading: { icon: Activity, color: "text-slate-400", label: t('checking') },
    healthy: {
      icon: CheckCircle,
      color: "text-green-500",
      label: t('healthy'),
    },
    degraded: {
      icon: AlertTriangle,
      color: "text-amber-500",
      label: t('degraded'),
    },
    down: { icon: XCircle, color: "text-red-500", label: t('down') },
  };

  const { icon: Icon, color, label } = statusConfig[health.status];

  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon className={`w-4 h-4 ${color}`} aria-hidden="true" />
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      {health.ageMinutes < 999 && (
        <span className="text-slate-400 text-xs">
          {t('updatedAgo', {minutes: health.ageMinutes})}
        </span>
      )}
    </div>
  );
}
