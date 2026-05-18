"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Download, ExternalLink, FileText, X } from "lucide-react";
import type { NewsItem } from "@/lib/types";
import { INDUSTRY_MAP } from "@/lib/constants";

interface Props {
  item: NewsItem | null;
  onClose: () => void;
}

export function MiniReportModal({ item, onClose }: Props) {
  const industry = item ? INDUSTRY_MAP[item.industry] ?? INDUSTRY_MAP.other : null;

  return (
    <AnimatePresence>
      {item && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 py-5 backdrop-blur-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.article
            role="dialog"
            aria-modal="true"
            aria-label={item.title}
            className="max-h-[92vh] w-full max-w-4xl overflow-hidden rounded-xl border border-line-3 bg-bg-1 shadow-2xl"
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            onClick={(event) => event.stopPropagation()}
          >
            <header className="flex items-center gap-3 border-b border-line-1 bg-bg-2/80 px-5 py-4">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.1em] text-fg-3">
                  {industry && <span style={{ color: industry.color }}>{industry.name}</span>}
                  <span>{item.region === "VN" ? "Vietnam" : "International"}</span>
                  <span>{item.bucket === "corp" ? "Corporate" : "Macro"}</span>
                  <span className="mono">{item.publishedAt.slice(0, 10)}</span>
                </div>
                <h2 className="mt-1 truncate text-[18px] font-semibold text-fg-0">{item.title}</h2>
              </div>
              <a
                href={item.source.url || "#"}
                target="_blank"
                rel="noreferrer"
                className="hidden items-center gap-2 rounded-lg border border-line-2 bg-bg-1 px-3 py-2 text-xs text-fg-1 hover:border-line-3 hover:bg-bg-3 md:inline-flex"
              >
                <ExternalLink className="size-3.5" />
                Original
              </a>
              <button
                onClick={onClose}
                className="flex size-9 items-center justify-center rounded-lg border border-line-2 bg-bg-1 text-fg-1 hover:border-line-3 hover:bg-bg-3"
                title="Close mini report"
              >
                <X className="size-4" />
              </button>
            </header>

            <div className="max-h-[calc(92vh-74px)] overflow-y-auto">
              <div className="grid gap-0 lg:grid-cols-[1fr_260px]">
                <main className="px-5 py-6 md:px-8">
                  <p className="border-l-2 border-accent pl-4 text-[21px] font-semibold leading-[1.35] tracking-tight text-fg-0">
                    {item.thesis}
                  </p>

                  <MemoSection title="Arguments">
                    <BulletList items={item.bullets} />
                  </MemoSection>

                  <MemoSection title="Supporting Insights">
                    <BulletList
                      items={[
                        `Source quality is marked ${item.confidence}; treat this as ${item.confidence === "high" ? "high-conviction source evidence" : "a signal requiring follow-up confirmation"}.`,
                        item.entities.length
                          ? `Named entities include ${item.entities.map((entity) => entity.ticker || entity.name).join(", ")}.`
                          : "No dominant listed entity was detected in the current structured payload.",
                        item.wikiPath
                          ? `The item is linked to the vault note ${item.wikiPath}.`
                          : "A linked wiki note has not been attached yet; sync should create or update one when processing completes.",
                      ]}
                    />
                  </MemoSection>

                  <MemoSection title="Key Implications">
                    <BulletList
                      items={[
                        item.region === "VN"
                          ? "Vietnam market read-through should be checked against sector peers and policy sensitivity before inclusion in the daily note."
                          : "International read-through should be mapped to Vietnam FX, trade, input-cost or sector-demand channels.",
                        item.bucket === "corp"
                          ? "Corporate impact is likely most relevant at the company, supply-chain, valuation, or earnings-expectation level."
                          : "Macro impact is likely most relevant through rates, FX, policy expectations, commodity prices, or cross-border flows.",
                      ]}
                    />
                  </MemoSection>

                  <MemoSection title="Original Source">
                    <div className="rounded-lg border border-line-1 bg-bg-2 p-4">
                      <div className="text-sm font-semibold text-fg-0">{item.source.name || "Original source"}</div>
                      <a
                        href={item.source.url || "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-2 inline-flex items-center gap-2 text-sm text-accent hover:underline"
                      >
                        Read Original Article
                        <ExternalLink className="size-3.5" />
                      </a>
                    </div>
                  </MemoSection>
                </main>

                <aside className="border-t border-line-1 bg-bg-0/70 p-5 lg:border-l lg:border-t-0">
                  <div className="text-[10.5px] font-semibold uppercase tracking-[0.14em] text-fg-3">A4 Summary</div>
                  <div className="mt-3 rounded-lg border border-line-2 bg-[#f8fafc] p-4 text-[#111827] shadow-lg">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6b7280]">Executive Memo</div>
                    <h3 className="mt-2 text-[15px] font-bold leading-tight">{item.title}</h3>
                    <ul className="mt-3 space-y-1.5 text-[11.5px] leading-snug">
                      {item.bullets.slice(0, 4).map((bullet, index) => (
                        <li key={index}>- {bullet}</li>
                      ))}
                    </ul>
                    <div className="mt-4 border-t border-[#d1d5db] pt-2 text-[10px] text-[#6b7280]">
                      {item.publishedAt.slice(0, 10)} / {item.confidence} confidence
                    </div>
                  </div>

                  <div className="mt-4 grid gap-2">
                    <a
                      href={`/api/v1/news/${item.id}/summary.pdf`}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-accent-line bg-accent-soft px-3 py-2 text-sm font-medium text-accent hover:bg-bg-3"
                    >
                      <Download className="size-4" />
                      Download A4 PDF
                    </a>
                    {item.wikiPath && (
                      <div className="inline-flex items-center gap-2 rounded-lg border border-line-1 bg-bg-2 px-3 py-2 text-xs text-fg-2">
                        <FileText className="size-3.5" />
                        <span className="truncate">{item.wikiPath}</span>
                      </div>
                    )}
                  </div>
                </aside>
              </div>
            </div>
          </motion.article>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function MemoSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-7">
      <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-fg-3">{title}</h3>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2.5 text-[14px] leading-[1.65] text-fg-1">
      {items.map((item, index) => (
        <li key={index} className="relative pl-5 before:absolute before:left-0 before:top-[0.75em] before:h-px before:w-2 before:bg-accent">
          {item}
        </li>
      ))}
    </ul>
  );
}
