"use client";

import { Download } from "lucide-react";

export function ReportViewer({ report }: { report: any }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
      <article className="glass rounded-xl2 p-8 prose prose-invert max-w-none">
        <div className="text-[10px] tracking-ultra text-accent-gold mb-2">
          {report.type.toUpperCase()} · {report.date}
        </div>
        <pre className="whitespace-pre-wrap font-sans text-[15px] leading-relaxed">
          {report.body_md}
        </pre>
      </article>
      <aside className="glass rounded-xl2 p-5 h-fit sticky top-24">
        <div className="text-[10px] tracking-ultra text-ink-dim mb-3">REPORT</div>
        {report.pdf_url ? (
          <a
            href={report.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 chip !text-ink-primary !bg-glass-hover"
          >
            <Download className="h-3.5 w-3.5" /> Download PDF
          </a>
        ) : (
          <div className="text-sm text-ink-dim">PDF not yet generated.</div>
        )}
      </aside>
    </div>
  );
}
