"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { NewsCard } from "./NewsCard";
import { MiniReportModal } from "./MiniReportModal";
import type { NewsItem } from "@/lib/types";

const SECTIONS = [
  {
    key: "vn-corp",
    title: "Vietnam Corporate News",
    eyebrow: "Industries, sectors, earnings, policy catalysts",
    region: "VN",
    bucket: "corp",
    topics: ["Banking", "Real Estate", "Technology", "Steel", "Consumer"],
  },
  {
    key: "int-corp",
    title: "International Corporate News",
    eyebrow: "Global companies with Vietnam read-through",
    region: "INT",
    bucket: "corp",
    topics: ["AI", "Semis", "Autos", "Financials", "Retail"],
  },
  {
    key: "vn-macro",
    title: "Vietnam Macro News",
    eyebrow: "Rates, FX, fiscal, trade, FDI and regulation",
    region: "VN",
    bucket: "macro",
    topics: ["SBV", "Tax", "FDI", "Trade", "Infrastructure"],
  },
  {
    key: "int-macro",
    title: "International Macro News",
    eyebrow: "Fed, China, commodities and geopolitical channels",
    region: "INT",
    bucket: "macro",
    topics: ["Fed", "China", "Oil", "USD", "ASEAN"],
  },
] as const;

export function IntelligenceFeed({ items }: { items: NewsItem[] }) {
  const [selected, setSelected] = useState<NewsItem | null>(null);
  const grouped = useMemo(
    () =>
      SECTIONS.map((section) => ({
        ...section,
        items: items
          .filter((item) => item.region === section.region && item.bucket === section.bucket)
          .sort((a, b) => b.publishedAt.localeCompare(a.publishedAt)),
      })),
    [items],
  );

  return (
    <div className="space-y-9">
      <MiniReportModal item={selected} onClose={() => setSelected(null)} />
      {grouped.map((section, sectionIndex) => (
        <motion.section
          key={section.key}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.36, ease: [0.2, 0.8, 0.2, 1], delay: 0.06 * sectionIndex }}
          className="rounded-xl border border-line-1 bg-bg-0/40 p-3"
        >
          <div className="mb-3 flex flex-wrap items-start gap-3 border-b border-line-1 px-1 pb-3">
            <div className="min-w-0 flex-1">
              <div className="text-[10.5px] font-semibold uppercase tracking-[0.14em] text-fg-3">{section.eyebrow}</div>
              <h3 className="mt-1 text-[18px] font-semibold tracking-tight text-fg-0">{section.title}</h3>
            </div>
            <div className="flex max-w-full flex-wrap gap-1.5">
              {section.topics.map((topic) => (
                <span key={topic} className="rounded-full border border-line-2 bg-bg-2 px-2.5 py-1 text-[11px] text-fg-2">
                  {topic}
                </span>
              ))}
            </div>
            <span className="mono rounded-md border border-line-2 bg-bg-2 px-2.5 py-1 text-[11px] text-fg-2">
              {section.items.length} items
            </span>
          </div>

          {section.items.length ? (
            <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
              {section.items.map((item) => (
                <NewsCard key={item.id} item={item} isNew={item.isNew} onOpen={setSelected} />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-line-2 bg-bg-1 px-4 py-8 text-center text-sm text-fg-3">
              No matching items in this section yet.
            </div>
          )}
        </motion.section>
      ))}
    </div>
  );
}
