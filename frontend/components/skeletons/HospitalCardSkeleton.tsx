export function HospitalCardSkeleton() {
  return (
    <div className="px-4 py-2">
      <div className="w-full text-left p-4 rounded-xl border border-border bg-card">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1 space-y-2">
            {/* Hospital Name Skeleton */}
            <div className="h-6 w-3/4 bg-muted rounded animate-pulse" />
            
            {/* Location Skeleton */}
            <div className="h-4 w-1/2 bg-muted rounded animate-pulse" />
          </div>

          <div className="flex flex-col items-end flex-shrink-0">
            {/* Wait Time Badge Skeleton */}
            <div className="h-8 w-20 bg-muted rounded-full animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}
