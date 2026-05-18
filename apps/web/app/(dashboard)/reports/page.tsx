import Link from "next/link";
import { listReports } from "@/lib/api";

export default async function ReportsPage() {
  const { items } = await listReports({});

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Report Center</h1>
      <p className="mt-1 text-sm text-fg-2">Institutional daily briefs, weekly synthesis, on-demand industry deep-dives.</p>

      <div className="mt-8 grid grid-cols-2 gap-4">
        {items.map((r) => (
          <Link key={r.id} href={`/reports/${r.id}`}
                className="block rounded-xl border border-line-2 bg-bg-1 p-5 transition hover:-translate-y-px hover:border-line-3">
            <div className="mb-2 flex items-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.1em] text-fg-3">
              <span className="text-accent">{r.type}</span>
              <span>·</span>
              <span className="mono">{r.publishedAt.slice(0, 10)}</span>
              <span className="ml-auto mono text-fg-3">v{r.version}</span>
            </div>
            <h2 className="text-[17px] font-semibold leading-snug tracking-tight">{r.title}</h2>
            <p className="mt-2 line-clamp-2 text-sm text-fg-1">{r.thesis}</p>
            <div className="mt-4 flex items-center gap-2 text-xs text-fg-2">
              <span>{r.sections.length} sections</span>
              <span>·</span>
              <span>PDF available</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
