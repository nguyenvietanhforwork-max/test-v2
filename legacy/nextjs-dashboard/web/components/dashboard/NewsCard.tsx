"use client";

import { motion } from "framer-motion";
import { FileText, ExternalLink, BookOpen } from "lucide-react";
import type { NewsItem } from "@/lib/types";
import { INDUSTRY_MAP } from "@/lib/constants";

interface Props {
  item: NewsItem;
  isNew?: boolean;
  onOpen?: (item: NewsItem) => void;
}

export function NewsCard({ item, isNew, onOpen }: Props) {
  const ind = INDUSTRY_MAP[item.industry] ?? INDUSTRY_MAP.other;
  const confidence = item.confidence === "high" ? 3 : item.confidence === "mid" ? 2 : 1;

  return (
    <motion.article
      layout
      whileHover={{ y: -1 }}
      transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
      onClick={() => onOpen?.(item)}
      className={`group relative cursor-pointer overflow-hidden rounded-xl border bg-bg-1 px-[18px] pb-4 pt-[18px] transition
        ${isNew ? "border-accent-line ring-amber" : "border-line-2 hover:border-line-3 hover:bg-bg-2"}`}
      style={{ ["--ind-color" as any]: ind.color }}
    >
      <span className="absolute left-0 top-0 bottom-0 w-[3px] opacity-70" style={{ background: ind.color }} />

      {isNew && (
        <span className="absolute right-2.5 top-2.5 size-1.5 animate-pulse-amber rounded-full bg-accent" />
      )}

      {/* Header */}
      <div className="mb-3 flex items-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.1em] text-fg-3">
        <span style={{ color: ind.color }}>{ind.name}</span>
        <Tag>{item.region}</Tag>
        <Tag>{item.bucket}</Tag>
        <span className="mono ml-auto text-fg-3">{item.publishedAt.slice(11, 16)} ICT</span>
      </div>

      {/* Confidence */}
      <div className="absolute right-4 top-4 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-fg-3">
        <span>{item.confidence}</span>
        <div className="flex gap-[2px]">
          {[0, 1, 2].map((i) => (
            <span key={i} className={`h-2 w-[3px] rounded-[1px] ${i < confidence ? "bg-accent" : "bg-fg-3/40"}`} />
          ))}
        </div>
      </div>

      {/* Thesis */}
      <h3 className="mb-3 text-[16px] font-semibold leading-[1.35] tracking-[-0.015em] text-fg-0">
        {item.thesis}
      </h3>

      {/* Bullets */}
      <ul className="space-y-1.5 text-[13px] leading-[1.55] text-fg-1">
        {item.bullets.map((b, i) => (
          <li key={i} className="relative pl-4 before:absolute before:left-0 before:top-[9px] before:h-px before:w-1.5 before:bg-fg-2">
            {b}
          </li>
        ))}
      </ul>

      {/* Footer */}
      <div className="mt-3.5 flex flex-wrap items-center gap-2 border-t border-line-1 pt-3.5 text-[11.5px]">
        {item.entities.slice(0, 3).map((e) => (
          <span key={e.slug} className="mono inline-flex items-center gap-1.5 rounded-md border border-line-2 bg-bg-2 px-2 py-0.5">
            {e.ticker && <span className="font-semibold text-accent">{e.ticker}</span>}
            <span>{e.name}</span>
          </span>
        ))}
        <span className="text-fg-3">{item.source.name}</span>
        <div className="ml-auto flex gap-1">
          <Action title="Open in vault"><FileText className="size-3" /></Action>
          <Action title="Open source" href={item.source.url}><ExternalLink className="size-3" /></Action>
          <Action title="Open report"><BookOpen className="size-3" /></Action>
        </div>
      </div>
    </motion.article>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded border border-line-2 bg-bg-3 px-1.5 py-px text-fg-1 tracking-[0.08em]">{children}</span>
  );
}

function Action({ children, title, href }: { children: React.ReactNode; title: string; href?: string }) {
  const className = "flex size-7 items-center justify-center rounded-md border border-line-1 text-fg-2 transition hover:border-line-3 hover:bg-bg-3 hover:text-fg-0";
  if (href) {
    return (
      <a title={title} href={href} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()} className={className}>
        {children}
      </a>
    );
  }
  return (
    <button title={title} onClick={(event) => event.stopPropagation()} className={className}>
      {children}
    </button>
  );
}
