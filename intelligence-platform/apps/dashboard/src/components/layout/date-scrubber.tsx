"use client";

import { useRouter, usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function DateScrubber() {
  const router = useRouter();
  const path = usePathname();
  const today = new Date();
  const currentStr = (() => {
    const m = path.match(/^\/daily\/(\d{4}-\d{2}-\d{2})/);
    return m ? m[1] : today.toISOString().slice(0, 10);
  })();
  const current = new Date(currentStr);
  const shift = (days: number) => {
    const d = new Date(current);
    d.setDate(d.getDate() + days);
    router.push(`/daily/${d.toISOString().slice(0, 10)}`);
  };
  const label = current.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  return (
    <div className="flex items-center gap-2">
      <button onClick={() => shift(-1)} className="p-1.5 rounded-md hover:bg-glass">
        <ChevronLeft className="h-4 w-4 text-ink-muted" />
      </button>
      <span className="font-editorial text-lg tracking-tight">{label}</span>
      <button onClick={() => shift(1)} className="p-1.5 rounded-md hover:bg-glass">
        <ChevronRight className="h-4 w-4 text-ink-muted" />
      </button>
    </div>
  );
}
