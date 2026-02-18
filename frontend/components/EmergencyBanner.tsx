import React from "react";
import { useTranslations } from "next-intl";

export function EmergencyBanner() {
  const t = useTranslations('Common.emergency');

  return (
    <div className="sticky top-0 z-50 bg-red-600 text-white px-4 py-2 text-center text-sm md:text-base font-medium shadow-md animate-in fade-in slide-in-from-top-2" role="alert">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2">
        <span className="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-5 h-5"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z"
              clipRule="evenodd"
            />
          </svg>
          {t('label')}
        </span>
        <span>
          {t('call')}{" "}
          <a
            href="tel:911"
            className="underline font-bold hover:text-red-100 transition-colors"
          >
            {t('number')}
          </a>{" "}
          {t('text')}
        </span>
      </div>
    </div>
  );
}
