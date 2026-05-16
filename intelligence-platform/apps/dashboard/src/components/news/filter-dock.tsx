"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { X } from "lucide-react";

const BUCKETS = ["vn_corp", "intl_corp", "vn_macro", "intl_macro"];
const INDUSTRIES = ["real-estate", "energy", "banking", "logistics", "agriculture", "automotive", "manufacturing"];

export function FilterDock() {
  const router = useRouter();
  const params = useSearchParams();
  const activeBucket = params.get("bucket");
  const activeIndustries = params.getAll("industry");

  const setParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(params.toString());
    if (value === null) next.delete(key);
    else next.set(key, value);
    router.push(`?${next.toString()}`, { scroll: false });
  };

  const toggleIndustry = (ind: string) => {
    const next = new URLSearchParams(params.toString());
    const arr = next.getAll("industry");
    if (arr.includes(ind)) {
      next.delete("industry");
      arr.filter((x) => x !== ind).forEach((x) => next.append("industry", x));
    } else next.append("industry", ind);
    router.push(`?${next.toString()}`, { scroll: false });
  };

  return (
    <div className="glass rounded-xl2 px-5 py-3 flex flex-wrap items-center gap-2">
      <span className="text-[10px] tracking-ultra text-ink-dim mr-2">FILTER</span>
      {BUCKETS.map((b) => (
        <button
          key={b}
          onClick={() => setParam("bucket", activeBucket === b ? null : b)}
          className={`chip ${activeBucket === b ? "!text-ink-primary !bg-glass-hover" : ""}`}
        >
          {b}
        </button>
      ))}
      <div className="w-px h-4 bg-border-subtle mx-2" />
      {INDUSTRIES.map((ind) => (
        <button
          key={ind}
          onClick={() => toggleIndustry(ind)}
          className={`chip ${activeIndustries.includes(ind) ? "!text-ink-primary !bg-glass-hover" : ""}`}
        >
          #{ind}
        </button>
      ))}
      {(activeBucket || activeIndustries.length > 0) && (
        <button
          onClick={() => router.push("?", { scroll: false })}
          className="chip text-ink-muted ml-auto"
        >
          <X className="h-3 w-3" /> clear
        </button>
      )}
    </div>
  );
}
