import { ComparabilityMatrix } from "@/components/methods/ComparabilityMatrix";
import { ProvinceMethodologyCard } from "@/components/methods/ProvinceMethodologyCard";
import { OntologyExplainer } from "@/components/methods/OntologyExplainer";
import { FAQ } from "@/components/methods/FAQ";
import { getDb } from "@/utils/db";

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

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <a
                href="/"
                className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-2"
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
                Back to Map
              </a>
              <h1 className="text-4xl font-bold text-slate-900 mb-2">
                Understanding Wait Time Metrics
              </h1>
              <p className="text-lg text-slate-600 max-w-3xl">
                Canadian provinces measure emergency department wait times using different
                methodologies. Direct comparison requires understanding these differences.
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="space-y-16">
          {/* Section 1: Comparability Matrix */}
          <section>
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-slate-900 mb-3">
                Provincial Comparability Matrix
              </h2>
              <p className="text-slate-600 leading-relaxed max-w-3xl">
                This matrix shows which provinces can be directly compared. Click any cell
                to see detailed methodology differences.
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
              <ComparabilityMatrix sources={sources} />
            </div>
          </section>

          {/* Section 2: Province Methodology Cards */}
          <section>
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-slate-900 mb-3">
                Provincial Methodologies
              </h2>
              <p className="text-slate-600 leading-relaxed max-w-3xl">
                Each province has chosen different measurement approaches based on their
                health system priorities and data infrastructure.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sources.map((source) => (
                <ProvinceMethodologyCard key={source.id} source={source} />
              ))}
            </div>
          </section>

          {/* Section 3: Ontology Explainer */}
          <section>
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
              <OntologyExplainer />
            </div>
          </section>

          {/* Section 4: FAQ */}
          <section>
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
              <FAQ />
            </div>
          </section>

          {/* Footer CTA */}
          <section className="text-center py-12">
            <div className="inline-block p-8 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xl">
              <h3 className="text-2xl font-bold mb-3">
                Ready to explore wait times?
              </h3>
              <p className="text-blue-100 mb-6 max-w-md">
                Now that you understand how measurements differ, browse the interactive
                map with confidence.
              </p>
              <a
                href="/"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-white text-blue-600 font-semibold hover:bg-blue-50 transition-colors"
              >
                View Interactive Map
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
      <footer className="border-t border-slate-200 bg-white mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              WaitTime Canada - A Health Systems Observatory
            </span>
            <span>
              Last updated: {new Date().toLocaleDateString()}
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
