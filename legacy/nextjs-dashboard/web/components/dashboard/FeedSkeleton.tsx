 "use client";

export function FeedSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-48 rounded-xl border border-line-1 bg-bg-1 p-4">
          <div className="mb-3 flex gap-2">
            <Shimmer className="h-3 w-14" />
            <Shimmer className="h-3 w-10" />
            <Shimmer className="ml-auto h-3 w-12" />
          </div>
          <Shimmer className="mb-2 h-4 w-3/4" />
          <Shimmer className="mb-2 h-4 w-2/3" />
          <Shimmer className="mb-4 h-4 w-1/2" />
          <Shimmer className="h-3 w-full" />
        </div>
      ))}
    </div>
  );
}

function Shimmer({ className = "" }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded bg-bg-2 ${className}`}>
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.2s_infinite] bg-gradient-to-r from-transparent via-white/[0.04] to-transparent" />
      <style jsx>{`@keyframes shimmer { 100% { transform: translateX(100%); } }`}</style>
    </div>
  );
}
