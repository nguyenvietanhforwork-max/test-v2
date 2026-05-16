"use client";

import { motion } from "framer-motion";

export function Headline({ data }: { data: any }) {
  if (!data) return null;
  return (
    <motion.div
      className="glass rounded-xl2 px-7 py-6 relative overflow-hidden"
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 bg-gradient-card opacity-50 pointer-events-none" />
      <div className="relative">
        <div className="text-[10px] tracking-ultra text-accent-gold mb-2">DAILY THESIS</div>
        <h1 className="font-editorial text-3xl leading-tight">{data.title}</h1>
        {data.thesis && (
          <p className="mt-3 text-ink-muted leading-relaxed max-w-3xl">{data.thesis}</p>
        )}
      </div>
    </motion.div>
  );
}
