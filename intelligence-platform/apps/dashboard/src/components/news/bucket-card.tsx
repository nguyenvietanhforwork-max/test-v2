"use client";

import { ChevronRight } from "lucide-react";

type Item = { id: string; title: string; classification?: { bucket?: string; industries?: string[] } };

export function BucketCard({
  bucket,
  title,
  payload,
  items,
  onOpen,
}: {
  bucket: string;
  title: string;
  payload: { count: number; by_industry?: Record<string, number> };
  items: Item[];
  onOpen: (id: string) => void;
}) {
  const filtered = items.filter((i) => i.classification?.bucket === bucket).slice(0, 8);
  return (
    <div className="glass glass-hover rounded-xl2 p-5">
      <div className="flex items-baseline justify-between">
        <h2 className="font-editorial text-xl">{title}</h2>
        <span className="num text-sm">{payload?.count ?? 0}</span>
      </div>

      {payload?.by_industry && Object.keys(payload.by_industry).length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {Object.entries(payload.by_industry)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 6)
            .map(([k, v]) => (
              <span key={k} className="chip">
                {k} <span className="num text-[10px] ml-1">{v}</span>
              </span>
            ))}
        </div>
      )}

      <ul className="mt-4 divide-y divide-border-subtle">
        {filtered.length === 0 && (
          <li className="py-4 text-sm text-ink-dim italic">No items in this bucket today.</li>
        )}
        {filtered.map((it) => (
          <li
            key={it.id}
            onClick={() => onOpen(it.id)}
            className="py-2.5 cursor-pointer flex items-start gap-3 group"
          >
            <div className="flex-1 text-sm leading-snug group-hover:text-accent-signal transition-colors">
              {it.title}
              <div className="flex gap-1.5 mt-1.5">
                {(it.classification?.industries ?? []).slice(0, 3).map((ind) => (
                  <span key={ind} className="text-[10px] text-ink-dim">#{ind}</span>
                ))}
              </div>
            </div>
            <ChevronRight className="h-4 w-4 text-ink-dim group-hover:text-accent-signal mt-1" />
          </li>
        ))}
      </ul>
    </div>
  );
}
