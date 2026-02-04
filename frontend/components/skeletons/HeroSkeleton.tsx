export function HeroSkeleton() {
  return (
    <section className="relative py-12 px-4 md:py-20 lg:py-24 bg-gradient-to-b from-muted/50 to-background border-b border-border">
      <div className="container max-w-6xl mx-auto flex flex-col lg:flex-row items-center gap-10 lg:gap-16">
        <div className="flex-1 text-center lg:text-left space-y-6 w-full">
          {/* Badge Skeleton */}
          <div className="inline-flex h-8 w-48 bg-muted rounded-full animate-pulse mx-auto lg:mx-0" />

          {/* Title Skeleton */}
          <div className="space-y-2 mx-auto lg:mx-0 max-w-lg">
            <div className="h-12 w-full bg-muted rounded animate-pulse" />
            <div className="h-12 w-3/4 bg-muted rounded animate-pulse mx-auto lg:mx-0" />
          </div>

          {/* Description Skeleton */}
          <div className="h-20 w-full max-w-xl bg-muted rounded animate-pulse mx-auto lg:mx-0" />

          {/* Buttons Skeleton */}
          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start pt-2">
            <div className="h-12 w-40 bg-muted rounded-full animate-pulse" />
            <div className="h-6 w-32 bg-muted rounded animate-pulse" />
          </div>
        </div>

        {/* Live Preview Card Skeleton */}
        <div className="w-full max-w-sm lg:w-[400px]">
          <div className="bg-card rounded-3xl shadow-xl border border-border/50 p-6 h-[250px] relative overflow-hidden">
            <div className="flex justify-between items-center mb-6">
              <div className="h-4 w-32 bg-muted rounded animate-pulse" />
              <div className="h-6 w-16 bg-muted rounded-full animate-pulse" />
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <div className="h-6 w-3/4 bg-muted rounded animate-pulse" />
                <div className="h-4 w-1/2 bg-muted rounded animate-pulse" />
              </div>

              <div className="flex items-baseline gap-2 pt-2">
                <div className="h-16 w-24 bg-muted rounded animate-pulse" />
                <div className="h-6 w-16 bg-muted rounded animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
