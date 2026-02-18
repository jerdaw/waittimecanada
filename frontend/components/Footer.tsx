import Link from "next/link";
import { useTranslations } from "next-intl";

export function Footer() {
  const t = useTranslations('Common');
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-muted/30 mt-auto">
      <div className="container max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About Section */}
          <div className="space-y-3">
            <h3 className="font-semibold text-sm text-foreground">
              {t('title')}
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {t('description')}
            </p>
            <p className="text-xs text-muted-foreground">
              {t('footer.dataSources')}
            </p>
          </div>

          {/* Quick Links */}
          <div className="space-y-3">
            <h3 className="font-semibold text-sm text-foreground">{t('nav.resources')}</h3>
            <nav className="flex flex-col gap-2 text-sm" aria-label={t('nav.resources')}>
              <Link
                href="/methods"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('nav.methodology')}
              </Link>
              <Link
                href="/analytics"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('nav.analytics')}
              </Link>
              <Link
                href="/data-quality"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('nav.dataQuality')}
              </Link>
              <Link
                href="/faq"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('nav.faq')}
              </Link>
            </nav>
          </div>

          {/* Legal & Project Links */}
          <div className="space-y-3">
            <h3 className="font-semibold text-sm text-foreground">{t('nav.project')}</h3>
            <nav className="flex flex-col gap-2 text-sm" aria-label={t('nav.project')}>
              <a
                href="https://github.com/jerdaw/waittimecanada"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('nav.github')}
              </a>
              <Link
                href="/privacy"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('nav.privacy')}
              </Link>
              <Link
                href="/terms"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('nav.terms')}
              </Link>
            </nav>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-6 border-t border-border">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-muted-foreground">
            <p>{t('footer.copyright', {year})}</p>
            <div className="flex items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
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
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <span className="font-medium">
                  {t('emergency.disclaimer')}
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
