import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { EmergencyBanner } from "@/components/EmergencyBanner";
import { Footer } from "@/components/Footer";
import "../globals.css";

import { ServiceWorkerRegister } from "@/components/ServiceWorkerRegister";
import { InstallPrompt } from "@/components/InstallPrompt";
import { StructuredData } from "./structured-data";

import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const locales = ["en", "fr"];

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "Metadata" });

  return {
    metadataBase: new URL(
      process.env.NEXT_PUBLIC_BASE_URL ?? "https://wait-time.ca",
    ),
    title: t("title"),
    description: t("description"),
    keywords: t("keywords"),
    authors: [{ name: "Wait Time Canada Team" }],
    viewport: "width=device-width, initial-scale=1, maximum-scale=1",
    icons: {
      icon: "/favicon.ico",
    },
    manifest: "/manifest.json",
    other: {
      "geo.region": "CA-ON",
      "geo.placename": "Ontario",
      "geo.position": "43.6532;-79.3832",
      "revisit-after": "1 day",
      category: "health",
      classification: "Healthcare Information",
    },
  };
}

export default async function RootLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  // Validate that the incoming `locale` parameter is valid
  if (!locales.includes(locale as any)) notFound();

  // Providing all messages to the client
  // side is the easiest way to get started
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning className={inter.variable}>
      <body className="font-sans antialiased bg-background text-foreground transition-colors duration-300 flex flex-col min-h-screen">
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <StructuredData />
            <EmergencyBanner />
            <ServiceWorkerRegister />
            <InstallPrompt />
            {children}
            <Footer />
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
