"use client";

import Link from "next/link";

export function ReportCenter({ initial }: { initial: any[] }) {
  return (
    <div className="space-y-4">
      <h1 className="font-editorial text-3xl">Report Center</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {initial.map((r) => (
          <Link
            key={r.id}
            href={`/reports/${r.id}`}
            className="glass glass-hover rounded-xl2 p-5 block"
          >
            <div className="text-[10px] tracking-ultra text-accent-gold">{r.type.toUpperCase()}</div>
            <div className="font-editorial text-lg mt-2">{r.date}</div>
            <div className="text-xs text-ink-dim mt-1">v{r.version}</div>
            {r.pdf_url && <div className="chip mt-3">PDF available</div>}
          </Link>
        ))}
      </div>
    </div>
  );
}
