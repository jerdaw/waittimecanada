import { Header } from "@/components/Header";
import Link from "next/link";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy | WaitTime Canada",
  description:
    "Privacy policy and data handling practices for WaitTime Canada healthcare observatory.",
  alternates: {
    canonical: "/privacy",
  },
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-4">Privacy Policy</h1>
        <p className="text-muted-foreground mb-8">
          Last updated: February 12, 2026
        </p>

        <div className="prose prose-slate dark:prose-invert max-w-none space-y-8">
          {/* Overview */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Overview</h2>
            <p className="text-foreground/90 leading-relaxed">
              WaitTime Canada is a health systems observatory and portfolio
              project that collects publicly available emergency room wait time
              data from official provincial health authority websites. We are
              committed to transparency in our data handling practices.
            </p>
          </section>

          {/* What Data We Collect */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              What Data We Collect
            </h2>
            <div className="space-y-4 text-foreground/90">
              <div>
                <h3 className="text-lg font-medium mb-2">Public Health Data</h3>
                <p className="leading-relaxed">
                  We collect publicly available wait time data from official
                  provincial health authority sources:
                </p>
                <ul className="list-disc ml-6 mt-2 space-y-1">
                  <li>Hospital names and locations</li>
                  <li>Emergency room wait time estimates</li>
                  <li>Stretcher occupancy percentages (where available)</li>
                  <li>
                    Methodology metadata (metric definitions, calculation
                    methods)
                  </li>
                </ul>
                <p className="mt-2">
                  This data is already public and contains no personal health
                  information (PHI) or personally identifiable information
                  (PII).
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-2">Analytics Data</h3>
                <p className="leading-relaxed">
                  We do not use analytics tracking, cookies, or third-party
                  tracking scripts. We do not collect IP addresses, browser
                  fingerprints, or usage analytics.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium mb-2">No User Accounts</h3>
                <p className="leading-relaxed">
                  This platform does not require user registration, accounts, or
                  login. We do not collect names, email addresses, or any
                  personal information from visitors.
                </p>
              </div>
            </div>
          </section>

          {/* How We Use Data */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">How We Use Data</h2>
            <div className="text-foreground/90 space-y-2">
              <p className="leading-relaxed">
                We use publicly available health data to:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>Display current emergency room wait times</li>
                <li>
                  Analyze and document methodology differences across provinces
                </li>
                <li>Monitor data quality and detect anomalies</li>
                <li>
                  Generate aggregate statistics and temporal trend analysis
                </li>
                <li>Support health systems research and policy evaluation</li>
              </ul>
            </div>
          </section>

          {/* Data Sources */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Data Sources</h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed mb-3">
                All data is collected from official provincial sources:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>
                  <strong>Ontario:</strong> Ontario Health
                </li>
                <li>
                  <strong>Quebec:</strong> Ministère de la Santé et des Services
                  sociaux (MSSS)
                </li>
                <li>
                  <strong>Alberta:</strong> Alberta Health Services (AHS)
                </li>
                <li>
                  <strong>British Columbia:</strong> Provincial Health Services
                  Authority (PHSA)
                </li>
              </ul>
              <p className="mt-3 leading-relaxed">
                We do not collect data from patients, hospitals, or healthcare
                providers directly. All data originates from publicly accessible
                government websites.
              </p>
            </div>
          </section>

          {/* PIPEDA and PHIPA Compliance */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Canadian Privacy Law Compliance
            </h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">
                <strong>
                  PIPEDA (Personal Information Protection and Electronic
                  Documents Act):
                </strong>{" "}
                This project does not collect, use, or disclose personal
                information as defined by PIPEDA. We exclusively use aggregate,
                anonymized, publicly available health system data.
              </p>
              <p className="leading-relaxed">
                <strong>
                  PHIPA (Personal Health Information Protection Act - Ontario):
                </strong>{" "}
                This project does not handle personal health information (PHI).
                Wait time data does not identify individuals, reveal patient
                conditions, or contain health records.
              </p>
            </div>
          </section>

          {/* Data Retention */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Data Retention</h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed mb-2">
                We store historical wait time measurements for research and
                analysis purposes:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>
                  <strong>Raw measurements:</strong> Retained for 30 days, then
                  deleted
                </li>
                <li>
                  <strong>Aggregate summaries:</strong> Retained permanently for
                  temporal trend analysis
                </li>
                <li>
                  <strong>Methodology metadata:</strong> Retained permanently
                  for research documentation
                </li>
              </ul>
            </div>
          </section>

          {/* Third-Party Services */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Third-Party Services
            </h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">
                This platform uses the following third-party services:
              </p>
              <ul className="list-disc ml-6 space-y-2">
                <li>
                  <strong>Mapbox:</strong> Map tile rendering for hospital
                  location visualization. Mapbox may collect geolocation data
                  for map rendering. See{" "}
                  <a
                    href="https://www.mapbox.com/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Mapbox Privacy Policy
                  </a>
                  .
                </li>
                <li>
                  <strong>Neon PostgreSQL:</strong> Database hosting (data is
                  encrypted at rest and in transit).
                </li>
                <li>
                  <strong>Netlify:</strong> Frontend hosting with CDN caching.
                </li>
              </ul>
              <p className="leading-relaxed mt-3">
                We do not share data with advertising networks, data brokers, or
                marketing platforms.
              </p>
            </div>
          </section>

          {/* User Rights */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Your Rights</h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed mb-2">
                Since we do not collect personal information, traditional data
                subject rights (access, deletion, correction) do not apply.
                However:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>
                  You can view all data sources and methodology documentation at{" "}
                  <Link
                    href="/methods"
                    className="text-primary hover:underline"
                  >
                    /methods
                  </Link>
                </li>
                <li>
                  All source code is open source and available on{" "}
                  <a
                    href="https://github.com/jerdaw/waittimecanada"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    GitHub
                  </a>
                </li>
                <li>
                  Data quality reports are publicly visible at{" "}
                  <Link
                    href="/data-quality"
                    className="text-primary hover:underline"
                  >
                    /data-quality
                  </Link>
                </li>
              </ul>
            </div>
          </section>

          {/* Contact */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Contact</h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed">
                Questions about data handling practices? Contact us through:
              </p>
              <ul className="list-disc ml-6 mt-2">
                <li>
                  GitHub Issues:{" "}
                  <a
                    href="https://github.com/jerdaw/waittimecanada/issues"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    github.com/jerdaw/waittimecanada/issues
                  </a>
                </li>
                <li>Repository: See contact information in README</li>
              </ul>
            </div>
          </section>

          {/* Changes to Policy */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Changes to This Policy
            </h2>
            <p className="text-foreground/90 leading-relaxed">
              We may update this privacy policy as the project evolves. Changes
              will be reflected in the &quot;Last updated&quot; date above.
              Material changes will be documented in the project{" "}
              <Link href="/" className="text-primary hover:underline">
                CHANGELOG
              </Link>
              .
            </p>
          </section>

          {/* Disclaimer */}
          <section className="border-t border-border pt-6 mt-8">
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2 text-amber-900 dark:text-amber-200">
                Important Disclaimer
              </h3>
              <p className="text-amber-800 dark:text-amber-300 leading-relaxed">
                This is a data observatory and portfolio project, not a medical
                service. For medical emergencies, call 911. For health advice,
                contact your provincial health line (811 in most provinces).
              </p>
            </div>
          </section>

          {/* Related Links */}
          <section className="border-t border-border pt-6">
            <h2 className="text-xl font-semibold mb-4">Related Pages</h2>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/terms"
                className="text-primary hover:underline font-medium"
              >
                Terms of Use
              </Link>
              <Link
                href="/methods"
                className="text-primary hover:underline font-medium"
              >
                Methodology
              </Link>
              <Link
                href="/faq"
                className="text-primary hover:underline font-medium"
              >
                FAQ
              </Link>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
