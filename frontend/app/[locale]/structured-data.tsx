import Script from "next/script";
import { useTranslations } from "next-intl";

export function StructuredData() {
  const t = useTranslations('StructuredData');

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: t('faq.q1'),
        acceptedAnswer: {
          "@type": "Answer",
          text: t('faq.a1'),
        },
      },
      {
        "@type": "Question",
        name: t('faq.q2'),
        acceptedAnswer: {
          "@type": "Answer",
          text: t('faq.a2'),
        },
      },
      {
        "@type": "Question",
        name: t('faq.q3'),
        acceptedAnswer: {
          "@type": "Answer",
          text: t('faq.a3'),
        },
      },
    ],
  };

  const medicalWebPageSchema = {
    "@context": "https://schema.org",
    "@type": "MedicalWebPage",
    name: "WaitTime Canada",
    description: t('medicalPage.desc'),
    audience: {
      "@type": "Patient",
      audienceType: "public",
    },
    specialty: {
      "@type": "MedicalSpecialty",
      name: "Emergency Medicine",
    },
  };

  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "WaitTime Canada",
    url: "https://waittime.ca",
    logo: "https://waittime.ca/icon.png",
    sameAs: ["https://github.com/jerdaw/waittimecanada"],
  };

  const howToSchema = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    name: "How to explore Ontario ER wait time data",
    step: [
      {
        "@type": "HowToStep",
        name: t('howTo.step1.name'),
        text: t('howTo.step1.text'),
      },
      {
        "@type": "HowToStep",
        name: t('howTo.step2.name'),
        text: t('howTo.step2.text'),
      },
      {
        "@type": "HowToStep",
        name: t('howTo.step3.name'),
        text: t('howTo.step3.text'),
      },
    ],
  };

  return (
    <>
      <Script
        id="schema-faq"
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <Script
        id="schema-medical"
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(medicalWebPageSchema),
        }}
      />
      <Script
        id="schema-org"
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
      />
      <Script
        id="schema-howto"
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />
    </>
  );
}
