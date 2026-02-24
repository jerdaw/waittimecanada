"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Github, Linkedin, Mail } from "lucide-react";
import { useTranslations } from "next-intl";

export function AboutSection() {
  const [expanded, setExpanded] = useState(true);
  const t = useTranslations('AboutSection');

  return (
    <section className="bg-card border-b border-border/50 py-12 px-4">
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
            <span className="text-sm font-medium text-primary uppercase tracking-wide">
              {t('badge')}
            </span>
            <h2 className="text-2xl font-bold text-foreground mt-1">
              {t('title')}
            </h2>
          </div>
          {expanded ? (
            <ChevronUp className="w-6 h-6 text-muted-foreground flex-shrink-0" />
          ) : (
            <ChevronDown className="w-6 h-6 text-muted-foreground flex-shrink-0" />
          )}
        </button>

        {expanded && (
          <div className="mt-6 space-y-4 text-muted-foreground animate-in fade-in slide-in-from-top-4 duration-300">
            <p>{t.rich('p1', { strong: (chunks) => <strong className="text-foreground">{chunks}</strong> })}</p>
            <p>{t.rich('p2', { strong: (chunks) => <strong className="text-foreground">{chunks}</strong> })}</p>
            <p>{t.rich('p3', { em: (chunks) => <em>{chunks}</em> })}</p>

            <div className="flex items-center gap-6 pt-4 border-t border-border/50">
              <div className="flex items-center gap-3">
                <div
                  className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-lg"
                  aria-label={t('aria.avatar')}
                >
                  JD
                </div>
                <div>
                  <p className="font-semibold text-foreground">
                    {t('author.name')}
                  </p>
                  <p className="text-sm text-muted-foreground">{t('author.role')}</p>
                </div>
              </div>
              <div className="flex gap-3">
                <a
                  href="https://github.com/jerdaw/waittimecanada"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={t('aria.github')}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Github className="w-5 h-5" />
                </a>
                <a
                  href="https://linkedin.com/in/jeremyjdawson"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={t('aria.linkedin')}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Linkedin className="w-5 h-5" />
                </a>
                <a
                  href="mailto:jeremyjdawson@gmail.com"
                  className="text-muted-foreground hover:text-foreground transition-colors"
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
