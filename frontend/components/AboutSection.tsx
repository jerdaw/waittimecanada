"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Github, Linkedin, Mail } from "lucide-react";
import { useTranslations } from "next-intl";

export function AboutSection() {
  const [expanded, setExpanded] = useState(false);
  const t = useTranslations('AboutSection');

  return (
    <section className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between text-left hover:opacity-80 transition-opacity"
          aria-expanded={expanded}
          aria-label={
            expanded ? t('aria.collapse') : t('aria.expand')
          }
        >
          <div>
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide">
              {t('badge')}
            </span>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
              {t('title')}
            </h2>
          </div>
          {expanded ? (
            <ChevronUp className="w-6 h-6 text-slate-400 flex-shrink-0" />
          ) : (
            <ChevronDown className="w-6 h-6 text-slate-400 flex-shrink-0" />
          )}
        </button>

        {expanded && (
          <div className="mt-6 space-y-4 text-slate-600 dark:text-slate-300 animate-in fade-in slide-in-from-top-4 duration-300">
            <p dangerouslySetInnerHTML={{ __html: t.raw('p1') }} />
            <p dangerouslySetInnerHTML={{ __html: t.raw('p2') }} />
            <p dangerouslySetInnerHTML={{ __html: t.raw('p3') }} />

            <div className="flex items-center gap-6 pt-4 border-t border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div
                  className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg"
                  aria-label={t('aria.avatar')}
                >
                  JD
                </div>
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {t('author.name')}
                  </p>
                  <p className="text-sm text-slate-500">{t('author.role')}</p>
                </div>
              </div>
              <div className="flex gap-3">
                <a
                  href="https://github.com/jerdaw/waittimecanada"
                  className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                  aria-label={t('aria.github')}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Github className="w-5 h-5" />
                </a>
                <a
                  href="https://linkedin.com/in/jeremyjdawson"
                  className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                  aria-label={t('aria.linkedin')}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Linkedin className="w-5 h-5" />
                </a>
                <a
                  href="mailto:jeremyjdawson@gmail.com"
                  className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                  aria-label={t('aria.email')}
                >
                  <Mail className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
