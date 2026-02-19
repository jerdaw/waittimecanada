import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "https://wait-time.ca";
  const currentDate = new Date();
  const locales = ['en', 'fr'];

  const routes = [
    "",
    "/methods",
    "/analytics",
    "/data-quality",
    "/faq",
    "/privacy",
    "/terms",
  ];

  const sitemapEntries: MetadataRoute.Sitemap = [];

  for (const locale of locales) {
    for (const route of routes) {
      sitemapEntries.push({
        url: `${baseUrl}/${locale}${route}`,
        lastModified: currentDate,
        changeFrequency: route === "" ? "hourly" : route === "/analytics" || route === "/data-quality" ? "daily" : "monthly",
        priority: route === "" ? 1.0 : route === "/methods" ? 0.9 : 0.8,
      });
    }
  }

  return sitemapEntries;
}
