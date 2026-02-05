'use client';

import { useState, useEffect } from 'react';
import { Activity, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

type Status = 'healthy' | 'degraded' | 'down' | 'loading';

interface HealthData {
  status: Status;
  lastUpdate: string | null;
  ageMinutes: number;
  sourceCount: number;
}

export function SystemStatus() {
  const [health, setHealth] = useState<HealthData>({
    status: 'loading',
    lastUpdate: null,
    ageMinutes: 0,
    sourceCount: 0,
  });

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch('/api/health');
        const data = await res.json();

        // Calculate age from most recent update
        let ageMinutes = 999;
        if (data.last_update) {
          const lastUpdate = new Date(data.last_update);
          ageMinutes = Math.round((Date.now() - lastUpdate.getTime()) / 60000);
        }

        // Determine status based on overall health and age
        let status: Status = 'healthy';
        if (!data.healthy || ageMinutes > 120) {
          status = 'down';
        } else if (ageMinutes > 60) {
          status = 'degraded';
        }

        setHealth({
          status,
          lastUpdate: data.last_update,
          ageMinutes,
          sourceCount: data.sources?.length || 0,
        });
      } catch {
        setHealth({
          status: 'down',
          lastUpdate: null,
          ageMinutes: 999,
          sourceCount: 0,
        });
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const statusConfig = {
    loading: { icon: Activity, color: 'text-slate-400', label: 'Checking...' },
    healthy: {
      icon: CheckCircle,
      color: 'text-green-500',
      label: 'All Systems Operational',
    },
    degraded: {
      icon: AlertTriangle,
      color: 'text-amber-500',
      label: 'Data May Be Stale',
    },
    down: { icon: XCircle, color: 'text-red-500', label: 'Data Unavailable' },
  };

  const { icon: Icon, color, label } = statusConfig[health.status];

  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon className={`w-4 h-4 ${color}`} aria-hidden="true" />
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      {health.ageMinutes < 999 && (
        <span className="text-slate-400 text-xs">
          (updated {health.ageMinutes}m ago)
        </span>
      )}
    </div>
  );
}
