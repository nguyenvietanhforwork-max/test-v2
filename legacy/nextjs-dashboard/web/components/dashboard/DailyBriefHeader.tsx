"use client";

import { motion } from "framer-motion";
import type { DailyBrief } from "@/lib/types";

interface Props { brief: DailyBrief }

export function DailyBriefHeader({ brief }: Props) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.36, ease: [0.2, 0.8, 0.2, 1] }}
      className="relative overflow-hidden rounded-xl border border-line-2 px-8 py-7"
      style={{
        background:
          "linear-gradient(135deg, rgba(232,184,100,0.06), rgba(157,123,232,0.04) 50%, transparent 70%), linear-gradient(180deg, rgba(18,21,28,0.9), rgba(12,14,19,0.78))",
      }}
    >
      <div className="flex items-center gap-3 text-[11.5px] font-semibold uppercase tracking-[0.12em] text-fg-2">
        <span>Morning Brief</span>
        <span className="text-fg-3">·</span>
        <span className="mono">{brief.date}</span>
        <span className="text-fg-3">·</span>
        <span className="rounded-full border border-accent-line bg-accent-soft px-2.5 py-0.5 tracking-[0.08em] text-accent">Daily Thesis</span>
      </div>

      <h1 className="mt-3.5 max-w-3xl text-[32px] font-semibold leading-[1.2] tracking-[-0.025em]">
        {brief.thesis.split(/(<em>.*?<\/em>)/).map((part, i) =>
          part.startsWith("<em>") ? (
            <em key={i} className="serif font-normal not-italic text-accent">{part.replace(/<\/?em>/g, "")}</em>
          ) : (
            <span key={i}>{part}</span>
          )
        )}
      </h1>

      <p className="mono mt-3.5 max-w-3xl text-[15px] leading-[1.6] text-fg-1" style={{ fontFamily: "Inter" }}>
        {brief.subtitle}
      </p>

      <div className="mt-7 grid grid-cols-2 gap-5 border-t border-line-1 pt-6 xl:grid-cols-4 xl:gap-6">
        {brief.stats.map((s) => (
          <Stat key={s.label} {...s} />
        ))}
      </div>
    </motion.section>
  );
}

function Stat({ label, value, delta, deltaTone, sub }: { label: string; value: string; delta?: string; deltaTone?: "pos"|"neg"|"neutral"; sub?: string }) {
  const tone = deltaTone === "pos" ? "text-pos" : deltaTone === "neg" ? "text-neg" : "text-fg-2";
  return (
    <div>
      <div className="text-[10.5px] font-semibold uppercase tracking-[0.1em] text-fg-3">{label}</div>
      <div className="mono mt-1.5 text-[22px] font-semibold">{value}</div>
      {delta && <div className={`mono mt-px text-[11.5px] ${tone}`}>{delta}</div>}
      {sub && <div className="mono mt-px text-[11.5px] text-fg-2">{sub}</div>}
    </div>
  );
}
