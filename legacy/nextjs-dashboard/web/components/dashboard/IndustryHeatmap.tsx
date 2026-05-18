"use client";

import { motion } from "framer-motion";
import type { IndustryHeatmapData } from "@/lib/types";

export function IndustryHeatmap({ data }: { data: IndustryHeatmapData }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.36, ease: [0.2, 0.8, 0.2, 1], delay: 0.12 }}
      className="grid grid-cols-7 gap-1.5 rounded-xl border border-line-2 bg-bg-1 p-4"
    >
      {data.cells.map((c) => {
        const intensity = Math.min(85, c.volume * 12 + 8);
        const sentColor = c.sentiment > 0.1 ? "var(--pos)" : c.sentiment < -0.1 ? "var(--neg)" : "var(--fg-3)";
        const sentSign = c.sentiment > 0 ? "+" : "";
        return (
          <div
            key={c.slug}
            title={`${c.name}: ${c.volume} items`}
            className="relative aspect-[16/9] cursor-pointer overflow-hidden rounded-lg border border-line-1 bg-white/[0.02] p-3 transition hover:-translate-y-px hover:border-line-3 flex flex-col justify-between"
            style={{ ["--heat-color" as any]: c.color }}
          >
            <span
              className="pointer-events-none absolute inset-x-0 bottom-0 opacity-20 transition-[height]"
              style={{ height: `${intensity}%`, background: `linear-gradient(180deg, transparent, ${c.color})` }}
            />
            <div className="text-[11px] font-medium leading-[1.2]" style={{ color: c.color }}>{c.name}</div>
            <div>
              <div className="mono text-[13px] font-semibold text-fg-0">{c.volume}</div>
              <div className="mono text-[10.5px]" style={{ color: sentColor }}>{sentSign}{c.sentiment.toFixed(2)}</div>
            </div>
          </div>
        );
      })}
    </motion.div>
  );
}
