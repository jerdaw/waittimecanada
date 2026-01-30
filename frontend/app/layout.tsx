import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WaitTime Canada - ER Wait Time Observatory",
  description:
    "A health systems observatory auditing emergency room wait times across Canada with methodological transparency.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
