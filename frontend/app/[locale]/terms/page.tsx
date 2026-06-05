import { Header } from "@/components/Header";
import Link from "next/link";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Use | Wait Time Canada",
  description:
    "Terms of use, disclaimers, and acceptable use policy for Wait Time Canada.",
  alternates: {
    canonical: "/terms",
  },
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-4">Terms of Use</h1>
        <p className="text-muted-foreground mb-8">
          Last updated: February 12, 2026
        </p>

        <div className="prose prose-slate dark:prose-invert max-w-none space-y-8">
          {/* Acceptance */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Acceptance of Terms</h2>
            <p className="text-foreground/90 leading-relaxed">
              By accessing and using Wait Time Canada, you accept and agree to
              be bound by these Terms of Use. If you do not agree to these
              terms, please do not use this platform.
            </p>
          </section>

          {/* Project Description */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Project Description</h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">
                Wait Time Canada is a{" "}
                <strong>health systems observatory</strong> that collects
                publicly available emergency room wait time data from official
                provincial health authority websites and analyzes methodology
                differences across provinces.
              </p>
              <p className="leading-relaxed font-medium text-amber-700 dark:text-amber-400">
                This is an independent research project, not an official
                government service or medical information platform.
              </p>
            </div>
          </section>

          {/* No Medical Advice */}
          <section className="border-2 border-red-200 dark:border-red-800 rounded-lg p-6 bg-red-50 dark:bg-red-900/20">
            <h2 className="text-2xl font-semibold mb-4 text-red-900 dark:text-red-200">
              No Medical Advice
            </h2>
            <div className="text-red-800 dark:text-red-300 space-y-3">
              <p className="font-semibold leading-relaxed">
                Wait Time Canada does not provide medical advice, diagnosis,
                treatment, or triage services.
              </p>
              <ul className="list-disc ml-6 space-y-2">
                <li>
                  <strong>For life-threatening emergencies:</strong> Call 911
                  immediately
                </li>
                <li>
                  <strong>For health advice:</strong> Call your provincial
                  health line (811 in most provinces)
                </li>
                <li>
                  <strong>For urgent medical concerns:</strong> Visit your
                  nearest emergency room regardless of estimated wait times
                </li>
              </ul>
              <p className="font-medium mt-4 leading-relaxed">
                Never delay seeking emergency medical care based on wait time
                information. Clinical urgency always takes precedence over
                convenience.
              </p>
            </div>
          </section>

          {/* Data Accuracy */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Data Accuracy and Limitations
            </h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">
                <strong>
                  Wait time estimates are approximate and subject to rapid
                  change.
                </strong>{" "}
                Actual wait times depend on:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>Patient acuity (severity of condition)</li>
                <li>Number of patients already waiting</li>
                <li>Sudden influx of critical cases</li>
                <li>Staff and resource availability</li>
                <li>Time of day and seasonal factors</li>
              </ul>
              <p className="leading-relaxed mt-3">
                <strong>We do not guarantee:</strong>
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>Real-time accuracy of displayed wait times</li>
                <li>Completeness of hospital coverage</li>
                <li>Availability of data from all provinces</li>
                <li>Uninterrupted service or data freshness</li>
              </ul>
              <p className="leading-relaxed mt-3">
                Data quality issues, methodology changes, and source
                unavailability are tracked at{" "}
                <Link
                  href="/data-quality"
                  className="text-primary hover:underline"
                >
                  /data-quality
                </Link>
                .
              </p>
            </div>
          </section>

          {/* Methodology Divergence */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Methodology Differences
            </h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">
                <strong>
                  Different provinces use different wait time metrics.
                </strong>{" "}
                For example:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>
                  Some measure <strong>Triage-to-Doctor</strong> time
                </li>
                <li>
                  Others measure <strong>Registration-to-Doctor</strong> time
                </li>
                <li>
                  Some report <strong>90th percentile</strong> (P90) estimates
                </li>
                <li>
                  Others report <strong>average</strong> or{" "}
                  <strong>rolling average</strong> estimates
                </li>
              </ul>
              <p className="leading-relaxed mt-3">
                <strong>
                  Direct comparison of wait times across provinces may not be
                  valid.
                </strong>{" "}
                Our platform highlights these methodology differences to prevent
                misinterpretation. See{" "}
                <Link href="/methods" className="text-primary hover:underline">
                  /methods
                </Link>{" "}
                for full documentation.
              </p>
            </div>
          </section>

          {/* Acceptable Use */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Acceptable Use</h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">You may use this platform to:</p>
              <ul className="list-disc ml-6 space-y-1">
                <li>View current emergency room wait time estimates</li>
                <li>Understand methodology differences across provinces</li>
                <li>
                  Access data quality reports and anomaly detection information
                </li>
                <li>Export data for academic or research purposes</li>
                <li>Cite this project in academic work (see CITATION.cff)</li>
              </ul>
              <p className="leading-relaxed mt-3">
                <strong>You may not:</strong>
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>
                  Scrape or systematically download data beyond the provided
                  export features
                </li>
                <li>
                  Attempt to reverse-engineer, decompile, or disassemble the
                  platform
                </li>
                <li>Use the platform for any unlawful or fraudulent purpose</li>
                <li>
                  Misrepresent this platform as an official government service
                </li>
                <li>
                  Use data to make medical decisions without consulting
                  healthcare providers
                </li>
              </ul>
            </div>
          </section>

          {/* Intellectual Property */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Intellectual Property
            </h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">
                <strong>Source Code:</strong> This project is open source under
                the MIT License. See{" "}
                <a
                  href="https://github.com/jerdaw/waittimecanada"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  GitHub repository
                </a>{" "}
                for full license terms.
              </p>
              <p className="leading-relaxed">
                <strong>Data Sources:</strong> Wait time data originates from
                provincial health authorities and remains subject to their
                respective terms and licenses. We do not claim ownership of
                source data.
              </p>
              <p className="leading-relaxed">
                <strong>Aggregated Analysis:</strong> Original analysis,
                methodology documentation, and aggregate statistics produced by
                this platform are available under the MIT License.
              </p>
            </div>
          </section>

          {/* Attribution */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Attribution and Citation
            </h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed mb-2">
                If you use data or analysis from this platform in academic work,
                please cite:
              </p>
              <div className="bg-muted p-4 rounded-lg font-mono text-sm my-4">
                Wait Time Canada: A Health Systems Observatory
                <br />
                https://github.com/jerdaw/waittimecanada
                <br />
                See CITATION.cff for structured citation metadata
              </div>
              <p className="leading-relaxed">
                Always attribute original data sources (Health Quality Ontario,
                Quebec MSSS, Alberta AHS, BC PHSA) when using or republishing
                wait time data.
              </p>
            </div>
          </section>

          {/* Limitation of Liability */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Limitation of Liability
            </h2>
            <div className="text-foreground/90 space-y-3">
              <p className="leading-relaxed">
                This platform is provided <strong>&quot;as is&quot;</strong>{" "}
                without warranties of any kind, express or implied. To the
                maximum extent permitted by law:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>
                  We make no warranties regarding data accuracy, completeness,
                  or reliability
                </li>
                <li>
                  We are not liable for decisions made based on information
                  provided
                </li>
                <li>
                  We are not responsible for service interruptions or data
                  unavailability
                </li>
                <li>
                  We are not liable for any direct, indirect, incidental, or
                  consequential damages
                </li>
              </ul>
              <p className="leading-relaxed mt-3 font-medium">
                Use of this platform for medical decision-making is entirely at
                your own risk.
              </p>
            </div>
          </section>

          {/* Service Modifications */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Service Modifications and Termination
            </h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed">
                As an independent public-interest project, we reserve the right
                to:
              </p>
              <ul className="list-disc ml-6 space-y-1">
                <li>Modify, suspend, or discontinue the service at any time</li>
                <li>Change features, data sources, or coverage areas</li>
                <li>Update these terms of use as the project evolves</li>
              </ul>
              <p className="leading-relaxed mt-3">
                Material changes will be reflected in the &quot;Last
                updated&quot; date and documented in the project CHANGELOG.
              </p>
            </div>
          </section>

          {/* Third-Party Links */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">
              Third-Party Links and Services
            </h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed">
                This platform links to official provincial health authority
                websites and may use third-party services (Mapbox, hosting
                providers). We are not responsible for the content, accuracy, or
                availability of third-party websites or services.
              </p>
            </div>
          </section>

          {/* Governing Law */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Governing Law</h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed">
                These terms are governed by the laws of Canada and the province
                of Ontario. Any disputes shall be resolved in the courts of
                Ontario.
              </p>
            </div>
          </section>

          {/* Contact */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Contact</h2>
            <div className="text-foreground/90">
              <p className="leading-relaxed">
                Questions about these terms? Contact us through:
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

          {/* Acknowledgment */}
          <section className="border-t border-border pt-6">
            <h2 className="text-xl font-semibold mb-4">Acknowledgment</h2>
            <p className="text-foreground/90 leading-relaxed">
              By using this platform, you acknowledge that you have read,
              understood, and agree to be bound by these Terms of Use. You also
              acknowledge that this is not a medical service and that you will
              seek professional medical advice for health concerns.
            </p>
          </section>

          {/* Related Links */}
          <section className="border-t border-border pt-6">
            <h2 className="text-xl font-semibold mb-4">Related Pages</h2>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/privacy"
                className="text-primary hover:underline font-medium"
              >
                Privacy Policy
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
