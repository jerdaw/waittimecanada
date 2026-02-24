import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { FAQAccordion } from "@/components/FAQAccordion";
import { Metadata } from "next";
import { getTranslations } from "next-intl/server";

export const metadata: Metadata = {
  title: "Frequently Asked Questions | Wait Time Canada",
  description:
    "Common questions about ER wait times, our methodology, and how we compare hospital data across provinces.",
  alternates: {
    canonical: "/faq",
  },
};

const FAQ_KEYS = ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9"] as const;

export default async function FAQPage() {
  const t = await getTranslations('FAQPage');

  const faqItems = FAQ_KEYS.map((key) => ({
    question: t(`items.${key}.question`),
    answer: t(`items.${key}.answer`),
  }));

  /* JSON-LD for SEO */
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqItems.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: typeof item.answer === "string" ? item.answer : "Check our website for details.",
      },
    })),
  };

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Header />

      <div className="container px-4 py-12 max-w-3xl mx-auto flex-1">
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
            {t('title')}
          </h1>
          <p className="text-lg text-muted-foreground">
            {t('subtitle')}
          </p>
        </div>

        <FAQAccordion items={faqItems} />

        <div className="mt-12 p-6 bg-muted/30 rounded-xl border border-border text-center">
          <h3 className="font-semibold mb-2">{t('cta.title')}</h3>
          <p className="text-muted-foreground text-sm mb-4">
            {t('cta.subtitle')}
          </p>
          <a
            href="/methods"
            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
          >
            {t('cta.button')}
          </a>
        </div>
      </div>

      <Footer />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </main>
  );
}
