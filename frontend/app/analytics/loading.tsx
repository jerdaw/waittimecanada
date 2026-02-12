import { Header } from "@/components/Header";

export default function AnalyticsLoading() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Page Header Skeleton */}
        <div className="mb-8 space-y-3">
          <div className="h-8 w-64 bg-muted rounded animate-pulse" />
          <div className="h-5 w-96 bg-muted rounded animate-pulse" />
        </div>

        {/* Stats Cards Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-card border border-border rounded-lg p-6 space-y-3"
            >
              <div className="h-4 w-24 bg-muted rounded animate-pulse" />
              <div className="h-10 w-32 bg-muted rounded animate-pulse" />
              <div className="h-3 w-40 bg-muted rounded animate-pulse" />
            </div>
          ))}
        </div>

        {/* System Trend Chart Skeleton */}
        <div className="bg-card border border-border rounded-lg p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <div className="h-6 w-48 bg-muted rounded animate-pulse" />
            <div className="h-9 w-32 bg-muted rounded animate-pulse" />
          </div>
          <div className="h-64 bg-muted rounded animate-pulse" />
        </div>

        {/* Region Dashboard Skeleton */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="h-6 w-56 bg-muted rounded animate-pulse mb-6" />
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 bg-muted/50 rounded"
              >
                <div className="flex-1 space-y-2">
                  <div className="h-5 w-48 bg-muted rounded animate-pulse" />
                  <div className="h-4 w-32 bg-muted rounded animate-pulse" />
                </div>
                <div className="flex gap-6">
                  <div className="h-8 w-20 bg-muted rounded animate-pulse" />
                  <div className="h-8 w-20 bg-muted rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
