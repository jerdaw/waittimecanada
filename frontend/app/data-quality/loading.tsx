import { Header } from "@/components/Header";

export default function DataQualityLoading() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Page Header Skeleton */}
        <div className="mb-8 space-y-2">
          <div className="h-8 w-80 bg-muted rounded animate-pulse" />
          <div className="h-5 w-96 bg-muted rounded animate-pulse" />
        </div>

        {/* Overall Status Card Skeleton */}
        <div className="bg-card border border-border rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="h-6 w-40 bg-muted rounded animate-pulse" />
            <div className="h-8 w-24 bg-muted rounded-full animate-pulse" />
          </div>
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="text-center space-y-2">
                <div className="h-8 w-16 bg-muted rounded animate-pulse mx-auto" />
                <div className="h-4 w-24 bg-muted rounded animate-pulse mx-auto" />
              </div>
            ))}
          </div>
        </div>

        {/* Source Quality Cards Skeleton */}
        <div className="space-y-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="space-y-2 flex-1">
                  <div className="h-6 w-48 bg-muted rounded animate-pulse" />
                  <div className="h-4 w-32 bg-muted rounded animate-pulse" />
                </div>
                <div className="h-8 w-20 bg-muted rounded-full animate-pulse" />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                {[1, 2, 3, 4].map((j) => (
                  <div key={j} className="space-y-2">
                    <div className="h-4 w-20 bg-muted rounded animate-pulse" />
                    <div className="h-7 w-16 bg-muted rounded animate-pulse" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Anomaly Feed Skeleton */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="h-6 w-48 bg-muted rounded animate-pulse mb-6" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="flex items-center gap-4 p-3 bg-muted/30 rounded"
              >
                <div className="h-10 w-10 bg-muted rounded-full animate-pulse shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-full bg-muted rounded animate-pulse" />
                  <div className="h-3 w-3/4 bg-muted rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
