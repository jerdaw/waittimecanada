interface Source {
  id: string;
  name: string;
  province: string;
  url: string;
  methodology_url: string | null;
  default_metric_family: string;
  default_start_event: string;
  default_end_event: string;
  default_statistic_type: string;
}

interface ProvinceMethodologyCardProps {
  source: Source;
}

const provinceColors: Record<string, { bg: string; border: string; accent: string }> = {
  Ontario: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    accent: "text-blue-700",
  },
  Quebec: {
    bg: "bg-indigo-50",
    border: "border-indigo-200",
    accent: "text-indigo-700",
  },
  Alberta: {
    bg: "bg-red-50",
    border: "border-red-200",
    accent: "text-red-700",
  },
  Manitoba: {
    bg: "bg-green-50",
    border: "border-green-200",
    accent: "text-green-700",
  },
  "British Columbia": {
    bg: "bg-purple-50",
    border: "border-purple-200",
    accent: "text-purple-700",
  },
};

const metricFamilyDescriptions: Record<string, string> = {
  TIME_TO_PROVIDER: "Time until first contact with physician or healthcare provider",
  TOTAL_LOS: "Complete length of stay in emergency department",
  STRETCHER_OCCUPANCY: "Percentage of stretchers currently occupied",
};

const startEventDescriptions: Record<string, string> = {
  TRIAGE: "Clock starts when patient completes triage assessment",
  REGISTRATION: "Clock starts when patient registers at ED",
  DOOR: "Clock starts when patient enters ED",
  UNKNOWN: "Start point varies or is not standardized",
};

const endEventDescriptions: Record<string, string> = {
  PHYSICIAN: "Clock stops at first physician contact",
  PROVIDER: "Clock stops at first healthcare provider contact (MD, NP, PA)",
  DISCHARGE: "Clock stops when patient is discharged",
  FIRST_ASSESSMENT: "Clock stops at initial clinical assessment",
};

const statisticTypeDescriptions: Record<string, string> = {
  P90: "90th percentile - 9 out of 10 patients seen faster than this",
  MEDIAN: "50th percentile - typical middle-of-the-road wait time",
  MEAN: "Average of all wait times",
  ROLLING_AVG: "Moving average over recent time period",
  ALGORITHMIC: "Calculated estimate based on current conditions",
  POINT_ESTIMATE: "Real-time snapshot of current wait",
};

export function ProvinceMethodologyCard({ source }: ProvinceMethodologyCardProps) {
  const colors = provinceColors[source.province] || {
    bg: "bg-slate-50",
    border: "border-slate-200",
    accent: "text-slate-700",
  };

  return (
    <div
      className={`
        rounded-xl border-2 ${colors.border} ${colors.bg}
        p-6 transition-all duration-200 hover:shadow-lg
      `}
    >
      {/* Header */}
      <div className="mb-4 pb-4 border-b-2 border-slate-200">
        <h3 className={`text-xl font-bold ${colors.accent} mb-1`}>
          {source.province}
        </h3>
        <p className="text-sm text-slate-600">{source.name}</p>
      </div>

      {/* Methodology details */}
      <div className="space-y-4">
        <MethodologyField
          label="Metric Family"
          value={source.default_metric_family}
          description={metricFamilyDescriptions[source.default_metric_family]}
        />
        <MethodologyField
          label="Start Event"
          value={source.default_start_event}
          description={startEventDescriptions[source.default_start_event]}
        />
        <MethodologyField
          label="End Event"
          value={source.default_end_event}
          description={endEventDescriptions[source.default_end_event]}
        />
        <MethodologyField
          label="Statistic Type"
          value={source.default_statistic_type}
          description={statisticTypeDescriptions[source.default_statistic_type]}
        />
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t-2 border-slate-200">
        {source.methodology_url ? (
          <a
            href={source.methodology_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              inline-flex items-center gap-2 text-sm font-medium
              ${colors.accent} hover:underline
            `}
          >
            View Official Methodology
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
        ) : (
          <span className="text-sm text-slate-500">
            Official methodology documentation not available
          </span>
        )}
      </div>
    </div>
  );
}

function MethodologyField({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description?: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
          {label}
        </span>
        <code className="px-2 py-1 rounded bg-white text-xs font-mono text-slate-700 border border-slate-200">
          {value}
        </code>
      </div>
      {description && (
        <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
      )}
    </div>
  );
}
