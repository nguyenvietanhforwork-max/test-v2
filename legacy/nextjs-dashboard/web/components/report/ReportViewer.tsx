"use client";

import { Download, Share2, History } from "lucide-react";
import type { Report } from "@/lib/types";

export function ReportViewer({ report }: { report: Report }) {
  return (
    <div className="grid h-[calc(100vh-56px-56px)] grid-cols-[1fr_360px] gap-0">
      <PdfPane url={report.pdfUrl} title={report.title} />
      <RightPane report={report} />
    </div>
  );
}

function PdfPane({ url, title }: { url?: string | null; title: string }) {
  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-3 border-b border-line-1 px-5 py-3">
        <div className="text-sm font-semibold">{title}</div>
        <span className="mono ml-2 text-xs text-fg-3">PDF · 12 pages</span>
        <div className="ml-auto flex gap-2">
          <IconBtn><History className="size-4" /></IconBtn>
          <IconBtn><Share2 className="size-4" /></IconBtn>
          {url && (
            <a href={url} className="flex size-8 items-center justify-center rounded-md border border-line-2 text-fg-1 hover:border-line-3 hover:bg-bg-2" title="Download PDF">
              <Download className="size-4" />
            </a>
          )}
        </div>
      </div>
      {url ? (
        <iframe src={url} className="flex-1 bg-bg-1" title="PDF" />
      ) : (
        <div className="flex flex-1 items-center justify-center bg-bg-1 px-6 text-center text-sm text-fg-2">
          PDF generation is queued. The markdown report remains available in the side panel.
        </div>
      )}
    </div>
  );
}

function RightPane({ report }: { report: Report }) {
  return (
    <aside className="overflow-y-auto border-l border-line-1 px-5 pb-10 pt-5">
      <h3 className="text-[10.5px] font-semibold uppercase tracking-[0.14em] text-fg-3">Sections</h3>
      <ul className="mt-3 space-y-1">
        {report.sections.map((s) => (
          <li key={s.id} className="rounded-md px-2 py-1.5 text-[13px] hover:bg-bg-2">{s.heading}</li>
        ))}
      </ul>

      <h3 className="mt-8 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-fg-3">Sources</h3>
      <ul className="mt-3 space-y-1.5">
        {report.sections.flatMap((s) => s.sources).slice(0, 12).map((src) => (
          <li key={src.newsId} className="text-[12.5px] text-fg-1">
            <a href={src.url} className="hover:text-accent">{src.title}</a>
          </li>
        ))}
      </ul>
    </aside>
  );
}

function IconBtn({ children }: { children: React.ReactNode }) {
  return (
    <button className="flex size-8 items-center justify-center rounded-md border border-line-2 text-fg-1 hover:border-line-3 hover:bg-bg-2">
      {children}
    </button>
  );
}
