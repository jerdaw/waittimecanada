import { Header } from "@/components/Header";
import { FAQAccordion } from "@/components/FAQAccordion";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Frequently Asked Questions | Wait Time Canada",
  description:
    "Common questions about ER wait times, our methodology, and how we compare hospital data across provinces.",
  alternates: {
    canonical: "/faq",
  },
};

export default function FAQPage() {
  const faqItems = [
    {
      question: "Are these wait times official?",
      answer: (
        <>
          <p className="mb-2">
            We collect data directly from official provincial health sources
            (e.g., Ontario Health, Health Quebec). However, we are an
            independent observatory, not a government agency.
          </p>
          <p>
            Always rely on professional medical advice. If you have a medical
            emergency, call 911 immediately.
          </p>
        </>
      ),
    },
    {
      question: "Why do wait times change so quickly?",
      answer:
        "ER wait times are dynamic and depend on the number of patients arriving, the severity of their conditions (triage scores), and available staff. A sudden influx of critical cases can increase wait times for everyone else instantly.",
    },
    {
      question: "What does 'Triage to Doctor' mean?",
      answer:
        "This metric measures the time from when a nurse first assesses you (triage) to when you see a physician. This is different from 'Registration to Doctor' or 'Total Time in ER'. Different provinces use different metrics, which is why we clearly label them.",
    },
    {
      question: "How often is data updated?",
      answer:
        "Most data sources are updated every 15-30 minutes. We fetch the latest data continuously. Check the 'Last updated' timestamp on each hospital card to be sure.",
    },
    {
      question: "Why does my local hospital show 'No Data'?",
      answer:
        "Not all hospitals report real-time wait times publicly. We can only display data that is officially published by the health authority. We are constantly working to add more sources.",
    },
  ];

  /* JSON-LD for SEO */
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqItems.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text:
          typeof item.answer === "string"
            ? item.answer
            : "Check our website for details.", // Simplified for JSON-LD
      },
    })),
  };

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Header />

      <div className="container px-4 py-12 max-w-3xl mx-auto flex-1">
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
            Frequently Asked Questions
          </h1>
          <p className="text-lg text-muted-foreground">
            Understand how we track wait times and what the data means for you.
          </p>
        </div>

        <FAQAccordion items={faqItems} />

        <div className="mt-12 p-6 bg-muted/30 rounded-xl border border-border text-center">
          <h3 className="font-semibold mb-2">Still have questions?</h3>
          <p className="text-muted-foreground text-sm mb-4">
            Learn more about how we standardize data across different provinces.
          </p>
          <a
            href="/methods"
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
          >
            View Methodology
          </a>
        </div>
      </div>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </main>
  );
}
