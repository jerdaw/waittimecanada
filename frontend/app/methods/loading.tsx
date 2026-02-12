import { Header } from "@/components/Header";

export default function MethodsLoading() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container max-w-5xl mx-auto px-4 sm:px-6 py-8 lg:py-12">
        {/* Page Header Skeleton */}
        <div className="mb-12 text-center space-y-3">
          <div className="h-10 w-96 bg-muted rounded animate-pulse mx-auto" />
          <div className="h-5 w-full max-w-2xl bg-muted rounded animate-pulse mx-auto" />
          <div className="h-5 w-full max-w-xl bg-muted rounded animate-pulse mx-auto" />
        </div>

        {/* Comparability Matrix Skeleton */}
        <div className="mb-12">
          <div className="h-7 w-64 bg-muted rounded animate-pulse mb-6" />
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <div className="p-4 space-y-3">
                {/* Table Header */}
                <div className="flex gap-4 pb-3 border-b border-border">
                  <div className="h-5 w-32 bg-muted rounded animate-pulse" />
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="h-5 w-24 bg-muted rounded animate-pulse"
                    />
                  ))}
                </div>
                {/* Table Rows */}
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex gap-4">
                    <div className="h-5 w-32 bg-muted rounded animate-pulse" />
                    {[1, 2, 3, 4].map((j) => (
                      <div
                        key={j}
                        className="h-5 w-24 bg-muted rounded animate-pulse"
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Province Methodology Cards Skeleton */}
        <div className="mb-12">
          <div className="h-7 w-72 bg-muted rounded animate-pulse mb-6" />
          <div className="grid gap-6 md:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-card border border-border rounded-lg p-6"
              >
                <div className="space-y-4">
                  <div className="h-6 w-40 bg-muted rounded animate-pulse" />
                  <div className="space-y-2">
                    <div className="h-4 w-full bg-muted rounded animate-pulse" />
                    <div className="h-4 w-5/6 bg-muted rounded animate-pulse" />
                    <div className="h-4 w-4/6 bg-muted rounded animate-pulse" />
                  </div>
                  <div className="pt-4 border-t border-border">
                    <div className="h-4 w-32 bg-muted rounded animate-pulse mb-2" />
                    <div className="space-y-1">
                      <div className="h-3 w-full bg-muted rounded animate-pulse" />
                      <div className="h-3 w-full bg-muted rounded animate-pulse" />
                      <div className="h-3 w-3/4 bg-muted rounded animate-pulse" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Ontology Explainer Skeleton */}
        <div className="mb-12 bg-muted/30 rounded-lg p-8">
          <div className="h-7 w-80 bg-muted rounded animate-pulse mb-6 mx-auto" />
          <div className="space-y-3 max-w-2xl mx-auto">
            <div className="h-4 w-full bg-muted rounded animate-pulse" />
            <div className="h-4 w-full bg-muted rounded animate-pulse" />
            <div className="h-4 w-5/6 bg-muted rounded animate-pulse" />
          </div>
        </div>

        {/* Data Export Skeleton */}
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="h-6 w-48 bg-muted rounded animate-pulse mb-4" />
          <div className="space-y-4">
            <div className="h-10 w-full bg-muted rounded animate-pulse" />
            <div className="h-10 w-full bg-muted rounded animate-pulse" />
          </div>
        </div>
      </main>
    </div>
  );
}
