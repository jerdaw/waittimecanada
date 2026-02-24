import { ComparabilityMatrix } from "@/components/methods/ComparabilityMatrix";
import { ProvinceMethodologyCard } from "@/components/methods/ProvinceMethodologyCard";
import { OntologyExplainer } from "@/components/methods/OntologyExplainer";
import { FAQ } from "@/components/methods/FAQ";
import { MethodologyTimeline } from "@/components/methods/MethodologyTimeline";
import { DataExport } from "@/components/DataExport";
import { getDb } from "@/utils/db";
import { getTranslations } from "next-intl/server";

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

const PROVINCE_NAMES: Record<string, string> = {
  QC: "Quebec",
  ON: "Ontario",
  AB: "Alberta",
  MB: "Manitoba",
  BC: "British Columbia",
  SK: "Saskatchewan",
  NS: "Nova Scotia",
  NB: "New Brunswick",
  PE: "Prince Edward Island",
  NL: "Newfoundland and Labrador",
  YT: "Yukon",
  NT: "Northwest Territories",
  NU: "Nunavut",
};

async function getSources(): Promise<Source[]> {
  try {
    const sql = getDb();
    const result = await sql<Source[]>`
      SELECT
        id,
        name,
        province,
        url,
        methodology_url,
        default_metric_family,
        default_start_event,
        default_end_event,
        default_statistic_type
      FROM sources
      ORDER BY province
    `;
    // Map province codes to full names
    return result.map((source) => ({
      ...source,
      province: PROVINCE_NAMES[source.province] || source.province,
    }));
  } catch (error) {
    console.error("Failed to fetch sources:", error);
    return [];
  }
}

export default async function MethodsPage() {
  const sources = await getSources();
  const t = await getTranslations('MethodsPage');

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <a
                href="/"
                className="inline-flex items-center gap-2 text-primary hover:text-primary/80 font-medium mb-2"
              >
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
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
                {t('header.backToMap')}
              </a>
              <h1 className="text-3xl font-bold text-foreground mb-2">
                {t('header.title')}
              </h1>
              <p className="text-lg text-muted-foreground max-w-3xl">
                {t('header.description')}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        <div className="space-y-12 md:space-y-16">
          {/* Section 1: Comparability Matrix */}
          <section>
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-foreground mb-3">
                {t('sections.comparabilityMatrix.title')}
              </h2>
              <p className="text-muted-foreground leading-relaxed max-w-3xl">
                {t('sections.comparabilityMatrix.description')}
              </p>
            </div>
            <div className="bg-card rounded-xl shadow-sm border border-border p-8">
              <ComparabilityMatrix sources={sources} />
            </div>
          </section>

          {/* Section 2: Province Methodology Cards */}
          <section>
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-foreground mb-3">
                {t('sections.provincialMethodologies.title')}
              </h2>
              <p className="text-muted-foreground leading-relaxed max-w-3xl">
                {t('sections.provincialMethodologies.description')}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sources.map((source) => (
                <ProvinceMethodologyCard key={source.id} source={source} />
              ))}
            </div>
          </section>

          {/* Section 3: Methodology Timeline */}
          <section>
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-foreground mb-3">
                {t('sections.methodologyTimeline.title')}
              </h2>
              <p className="text-muted-foreground leading-relaxed max-w-3xl">
                {t('sections.methodologyTimeline.description')}
              </p>
            </div>
            <div className="bg-card rounded-xl shadow-sm border border-border p-8">
              <MethodologyTimeline sources={sources} />
            </div>
          </section>

          {/* Section 4: Ontology Explainer */}
          <section>
            <div className="bg-card rounded-xl shadow-sm border border-border p-8">
              <OntologyExplainer />
            </div>
          </section>

          {/* Section 5: FAQ */}
          <section>
            <div className="bg-card rounded-xl shadow-sm border border-border p-8">
              <FAQ />
            </div>
          </section>

          {/* Section 6: Data for Researchers */}
          <section>
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-foreground mb-3">
                {t('sections.dataForResearchers.title')}
              </h2>
              <p className="text-muted-foreground leading-relaxed max-w-3xl">
                {t('sections.dataForResearchers.description')}
              </p>
            </div>
            <DataExport />
          </section>

          {/* Footer CTA */}
          <section className="text-center py-12">
            <div className="inline-block p-8 rounded-2xl bg-primary text-primary-foreground shadow-xl">
              <h3 className="text-2xl font-bold mb-3">
                {t('cta.title')}
              </h3>
              <p className="text-primary-foreground/80 mb-6 max-w-md">
                {t('cta.description')}
              </p>
              <a
                href="/"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-background text-primary font-semibold hover:bg-muted transition-colors"
              >
                {t('cta.button')}
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </a>
            </div>
          </section>
        </div>
      </main>

      {/* Page Footer */}
      <footer className="border-t border-border bg-card mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{t('footer.tagline')}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
