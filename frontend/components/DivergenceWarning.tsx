interface DivergenceWarningProps {
  message: string;
  variant?: "inline" | "banner" | "compact";
}

export function DivergenceWarning({
  message,
  variant = "inline",
}: DivergenceWarningProps) {
  if (variant === "compact") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-amber-100 text-amber-800 text-xs">
        <svg
          className="w-3 h-3 flex-shrink-0"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
        <span className="font-medium">Different methodologies</span>
      </div>
    );
  }

  if (variant === "banner") {
    return (
      <div className="rounded-xl border-2 border-amber-300 bg-amber-50 p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <svg
              className="w-6 h-6 text-amber-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-amber-900 text-sm mb-1">
              Methodology Divergence Warning
            </h4>
            <p className="text-amber-800 text-sm leading-relaxed">{message}</p>
            <a
              href="/methods"
              className="inline-flex items-center gap-1 mt-2 text-sm text-amber-700 hover:text-amber-900 font-medium"
            >
              Learn about methodologies
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>
    );
  }

  // inline variant (default)
  return (
    <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200">
      <svg
        className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fillRule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      <p className="text-sm text-amber-800 leading-relaxed">{message}</p>
    </div>
  );
}
