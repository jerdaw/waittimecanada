import { Header } from "@/components/Header";

export default function StatusLoading() {
  return (
    <div className="min-h-screen bg-muted/20">
      <Header />
      <main className="max-w-screen-lg mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Page Header Skeleton */}
        <div className="space-y-2">
          <div className="h-4 w-32 bg-muted rounded animate-pulse" />
          <div className="h-8 w-56 bg-muted rounded animate-pulse" />
          <div className="h-4 w-80 bg-muted rounded animate-pulse" />
        </div>

        {/* Overall Health Banner Skeleton */}
        <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-6 w-40 bg-muted rounded animate-pulse" />
            <div className="h-5 w-20 bg-muted rounded-full animate-pulse" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="text-center space-y-2">
                <div className="h-8 w-16 bg-muted rounded animate-pulse mx-auto" />
                <div className="h-3 w-24 bg-muted rounded animate-pulse mx-auto" />
              </div>
            ))}
          </div>
        </div>

        {/* Source Cards Skeleton */}
        <div className="space-y-4">
          <div className="h-6 w-48 bg-muted rounded animate-pulse" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="rounded-xl border border-border/50 bg-card p-4 space-y-3"
              >
                <div className="flex justify-between">
                  <div className="space-y-1">
                    <div className="h-4 w-36 bg-muted rounded animate-pulse" />
                    <div className="h-3 w-20 bg-muted rounded animate-pulse" />
                  </div>
                  <div className="h-5 w-16 bg-muted rounded-full animate-pulse" />
                </div>
                <div className="space-y-2">
                  {[1, 2, 3].map((j) => (
                    <div
                      key={j}
                      className="h-1.5 bg-muted rounded-full animate-pulse"
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
