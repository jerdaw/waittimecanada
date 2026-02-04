import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { EmergencyBanner } from "@/components/EmergencyBanner";
import "./globals.css";

import { ServiceWorkerRegister } from "@/components/ServiceWorkerRegister";
import { InstallPrompt } from "@/components/InstallPrompt";
import { StructuredData } from "./structured-data";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "WaitTime Canada - ER Wait Time Observatory",
  description:
    "A health systems observatory auditing emergency room wait times across Canada with methodological transparency.",
  manifest: "/manifest.json",
  other: {
    'geo.region': 'CA-ON',
    'geo.placename': 'Ontario',
    'geo.position': '43.6532;-79.3832',
    'revisit-after': '1 day',
    'category': 'health',
    'classification': 'Healthcare Information',
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body className="font-sans antialiased bg-background text-foreground transition-colors duration-300">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <StructuredData />
          <EmergencyBanner />
          <ServiceWorkerRegister />
          <InstallPrompt />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

