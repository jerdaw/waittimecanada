import Script from 'next/script';

export function StructuredData() {
  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "How does WaitTime Canada measure ER wait times?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "We aggregate data from provincial health authorities. For Ontario, we report P90 (90th percentile) wait times from triage to physician assessment."
        }
      },
      {
        "@type": "Question",
        "name": "Why can't I compare Ontario and Quebec wait times directly?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Ontario reports P90 (90th percentile) triage-to-physician times, while Quebec reports rolling average registration-to-physician times. These different methodologies mean direct comparison is statistically invalid."
        }
      },
      {
        "@type": "Question",
        "name": "Is this data real-time?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Yes, we scrape official provincial data sources every 15 minutes. Check the 'Updated' timestamp on each hospital card for specific data freshness."
        }
      }
    ]
  };

  const medicalWebPageSchema = {
    "@context": "https://schema.org",
    "@type": "MedicalWebPage",
    "name": "WaitTime Canada",
    "description": "Real-time emergency room wait times and methodology auditing for Canadian hospitals.",
    "audience": {
      "@type": "Patient",
      "audienceType": "public"
    },
    "specialty": {
      "@type": "MedicalSpecialty",
      "name": "Emergency Medicine"
    }
  };

  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "WaitTime Canada",
    "url": "https://waittime.ca",
    "logo": "https://waittime.ca/icon.png",
    "sameAs": [
      "https://github.com/jerdaw/waittimecanada"
    ]
  };

  const howToSchema = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "How to explore Ontario ER wait time data",
    "step": [
      {
        "@type": "HowToStep",
        "name": "Allow location access",
        "text": "Optionally enable browser geolocation to see hospitals sorted by distance."
      },
      {
        "@type": "HowToStep",
        "name": "Browse wait time data",
        "text": "Explore the publicly reported wait times from official provincial health sources."
      },
      {
        "@type": "HowToStep",
        "name": "Understand the methodology",
        "text": "Click on a hospital to learn how its wait time is measured and reported by provincial authorities."
      }
    ]
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
        dangerouslySetInnerHTML={{ __html: JSON.stringify(medicalWebPageSchema) }}
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
