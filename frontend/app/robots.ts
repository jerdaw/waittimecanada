import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "https://wait-time.ca";

  return {
    rules: [
      {
        userAgent: "*",
        allow: [
          "/",
          "/methods",
          "/analytics",
          "/data-quality",
          "/faq",
          "/privacy",
          "/terms",
        ],
        disallow: [
          "/api/",
          "/_next/",
          "/admin",
        ],
      },
      // Respect crawl rate limits (be polite to server resources)
      {
        userAgent: "GPTBot",
        disallow: "/", // Opt out of AI training scraping
      },
      {
        userAgent: "CCBot",
        disallow: "/", // Opt out of Common Crawl AI training
      },
      {
        userAgent: "ChatGPT-User",
        disallow: "/", // Opt out of ChatGPT browsing
      },
      {
        userAgent: "anthropic-ai",
        disallow: "/", // Opt out of Anthropic AI training
      },
      {
        userAgent: "Claude-Web",
        disallow: "/", // Opt out of Claude browsing
      },
      {
        userAgent: "Google-Extended",
        disallow: "/", // Opt out of Google Bard AI training
      },
      {
        userAgent: "PerplexityBot",
        disallow: "/", // Opt out of Perplexity AI
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
