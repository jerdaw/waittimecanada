import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { HomePageClient } from "./HomePageClient";
import { getPublicHospitals } from "@/utils/public-hospitals";
import { logger } from "@/utils/logger";

export const dynamic = "force-dynamic";

async function getInitialHomepageData() {
  try {
    return await getPublicHospitals({ province: "ON" });
  } catch (error) {
    logger.error("Failed to load server-rendered homepage data", error);
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Metadata" });
  const initialData = await getInitialHomepageData();
  const coverage = initialData?.coverage;
  const title = t("title");
  const description = coverage
    ? t("coverageDescription", {
        hospitals: coverage.hospital_count,
        provinces: coverage.province_count,
        date: coverage.generated_at.slice(0, 10),
      })
    : t("description");

  return {
    title,
    description,
    openGraph: {
      type: "website",
      url: "/" + locale,
      title,
      description,
      locale: locale === "fr" ? "fr_CA" : "en_CA",
    },
    twitter: {
      card: "summary",
      title,
      description,
    },
    other: coverage
      ? {
          "coverage:generated_at": coverage.generated_at,
          "coverage:hospital_count": String(coverage.hospital_count),
          "coverage:province_count": String(coverage.province_count),
        }
      : undefined,
  };
}

export default async function HomePage() {
  const initialData = await getInitialHomepageData();

  return (
    <HomePageClient
      initialHospitals={initialData?.data ?? []}
      initialCoverage={initialData?.coverage ?? null}
    />
  );
}
