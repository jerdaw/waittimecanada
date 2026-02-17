import { Header } from "@/components/Header";

export default function FAQLoading() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-3xl mx-auto px-4 py-12">
        {/* Page Header Skeleton */}
        <div className="text-center mb-12 space-y-3">
          <div className="h-10 w-96 bg-muted rounded animate-pulse mx-auto" />
          <div className="h-5 w-full max-w-xl bg-muted rounded animate-pulse mx-auto" />
        </div>

        {/* FAQ Items Skeleton */}
        <div className="space-y-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div
              key={i}
              className="bg-card border border-border rounded-lg p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-3">
                  <div className="h-6 w-full bg-muted rounded animate-pulse" />
                  <div className="h-4 w-5/6 bg-muted rounded animate-pulse" />
                </div>
                <div className="h-6 w-6 bg-muted rounded animate-pulse shrink-0" />
              </div>
            </div>
          ))}
        </div>

        {/* Contact Section Skeleton */}
        <div className="mt-16 text-center space-y-4 border-t border-border pt-12">
          <div className="h-6 w-64 bg-muted rounded animate-pulse mx-auto" />
          <div className="h-4 w-96 bg-muted rounded animate-pulse mx-auto" />
          <div className="flex justify-center gap-4 pt-4">
            <div className="h-10 w-32 bg-muted rounded animate-pulse" />
            <div className="h-10 w-32 bg-muted rounded animate-pulse" />
          </div>
        </div>
      </main>
    </div>
  );
}
