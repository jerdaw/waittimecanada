import { Header } from "@/components/Header";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="space-y-6">
          {/* 404 Icon */}
          <div className="mx-auto w-20 h-20 rounded-full bg-muted flex items-center justify-center">
            <svg
              className="w-10 h-10 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          {/* Error Message */}
          <div className="space-y-2">
            <h1 className="text-6xl font-bold text-foreground">404</h1>
            <h2 className="text-2xl font-semibold text-foreground">
              Page Not Found
            </h2>
            <p className="text-muted-foreground">
              The page you&apos;re looking for doesn&apos;t exist or has been
              moved.
            </p>
          </div>

          {/* Navigation Links */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
            <Link
              href="/"
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary-hover transition-colors"
            >
              Back to Homepage
            </Link>
            <Link
              href="/faq"
              className="px-6 py-3 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors"
            >
              View FAQ
            </Link>
          </div>

          {/* Helpful Links */}
          <div className="pt-8 border-t border-border mt-8">
            <p className="text-sm text-muted-foreground mb-4">
              Looking for something specific?
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <Link
                href="/methods"
                className="text-primary hover:underline font-medium"
              >
                Methodology
              </Link>
              <Link
                href="/analytics"
                className="text-primary hover:underline font-medium"
              >
                Analytics
              </Link>
              <Link
                href="/data-quality"
                className="text-primary hover:underline font-medium"
              >
                Data Quality
              </Link>
              <a
                href="https://github.com/jerdaw/waittimecanada"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline font-medium"
              >
                GitHub
              </a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
