'use client';

import { useState } from 'react';
import { Download, FileSpreadsheet, Code, Info } from 'lucide-react';

export function DataExport() {
  const [province, setProvince] = useState<string>('');
  const [dateRange, setDateRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d');
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);

    const params = new URLSearchParams();
    if (province) params.set('province', province);
    params.set('format', format);

    // Calculate date range
    const now = new Date();
    if (dateRange !== 'all') {
      const days = { '24h': 1, '7d': 7, '30d': 30 }[dateRange];
      const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      params.set('start_date', start.toISOString());
    }

    // Trigger download
    window.location.href = `/api/export?${params.toString()}`;

    // Reset loading state after a short delay (download is triggered but doesn't block)
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileSpreadsheet className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          Download Data
        </h3>
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
        Export wait time data with full methodology tags for research use.
        All exports include metric ontology columns for proper attribution.
      </p>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label htmlFor="province-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Province
          </label>
          <select
            id="province-select"
            value={province}
            onChange={(e) => setProvince(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          >
            <option value="">All Provinces</option>
            <option value="ON">Ontario</option>
            <option value="QC">Quebec</option>
            <option value="AB">Alberta</option>
          </select>
        </div>

        <div>
          <label htmlFor="daterange-select" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Date Range
          </label>
          <select
            id="daterange-select"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as any)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="all">All Data</option>
          </select>
        </div>
      </div>

      {/* Format Toggle */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Format:
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setFormat('csv')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              format === 'csv'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            CSV
          </button>
          <button
            onClick={() => setFormat('json')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              format === 'json'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
            }`}
          >
            <Code className="w-4 h-4" />
            JSON
          </button>
        </div>
      </div>

      {/* Download Button */}
      <button
        onClick={handleExport}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Download className="w-5 h-5" />
        {loading ? 'Preparing...' : 'Download Data'}
      </button>

      {/* Citation Info */}
      <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
          <div className="text-xs text-slate-500 dark:text-slate-400">
            <p className="font-medium mb-1">Suggested Citation:</p>
            <p className="italic">
              WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set].
              https://waittimecanada.ca
            </p>
            <p className="mt-2">License: CC-BY-4.0 (Attribution Required)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
