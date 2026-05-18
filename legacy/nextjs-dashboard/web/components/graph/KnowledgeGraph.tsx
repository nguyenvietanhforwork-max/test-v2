"use client";

import { useEffect, useRef } from "react";

/**
 * Knowledge Graph
 * ----------------
 * D3-force visualization of entity ↔ industry ↔ theme relationships.
 *
 * Implementation note: this is a skeleton — the real version pulls from
 * GET /graph?center=&depth=&window= and uses d3-force with a custom WebGL
 * renderer (pixi.js) for >5k node performance. The shape of the data is:
 *   { nodes: [{id, label, kind: 'entity'|'industry'|'theme', weight}],
 *     edges: [{source, target, weight}] }
 *
 * Interactions:
 *   - pinch / ctrl-scroll zoom
 *   - drag pan
 *   - click node → opens right rail entity detail
 *   - time scrubber (bottom) filters edges by window
 */
export function KnowledgeGraph() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // TODO: hook up d3-force here; placeholder visual below.
  }, []);

  return (
    <div className="relative h-full w-full">
      <div ref={ref} className="absolute inset-0">
        <Placeholder />
      </div>
      <TimeScrubber />
    </div>
  );
}

function Placeholder() {
  // Static SVG suggesting the rendered graph until d3-force is wired up.
  return (
    <svg viewBox="0 0 800 600" className="size-full">
      <defs>
        <radialGradient id="node-g" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.7" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </radialGradient>
      </defs>
      {[
        [400, 300, 32, "VIC"],
        [280, 220, 22, "VCB"],
        [520, 220, 24, "HPG"],
        [300, 400, 20, "FPT"],
        [520, 400, 22, "VHM"],
        [180, 320, 14, "MSN"],
        [620, 320, 16, "VJC"],
        [400, 140, 14, "KBC"],
        [400, 460, 14, "NLG"],
      ].map(([cx, cy, r, label], i) => (
        <g key={i}>
          <line x1={400} y1={300} x2={cx as number} y2={cy as number} stroke="var(--line-2)" strokeWidth={1} />
          <circle cx={cx as number} cy={cy as number} r={(r as number) + 12} fill="url(#node-g)" />
          <circle cx={cx as number} cy={cy as number} r={r as number} fill="var(--bg-2)" stroke="var(--accent)" strokeWidth={1.4} />
          <text x={cx as number} y={(cy as number) + 4} textAnchor="middle" fontFamily="JetBrains Mono" fontSize={11} fill="var(--fg-0)" fontWeight={600}>{label}</text>
        </g>
      ))}
    </svg>
  );
}

function TimeScrubber() {
  return (
    <div className="absolute bottom-6 left-1/2 z-20 -translate-x-1/2 rounded-xl border border-line-3 px-5 py-3 glass" style={{ minWidth: 560 }}>
      <div className="flex items-center gap-3 text-xs">
        {["24h", "7d", "30d", "All"].map((w, i) => (
          <button key={w} className={`rounded-full border px-3 py-1 ${i === 1 ? "border-accent-line bg-accent-soft text-accent" : "border-line-2 text-fg-2 hover:text-fg-0"}`}>{w}</button>
        ))}
        <span className="mx-3 h-4 w-px bg-line-2" />
        <input type="range" className="flex-1 accent-[var(--accent)]" defaultValue={60} />
        <span className="mono text-fg-3">2026.05.08 → 2026.05.15</span>
      </div>
    </div>
  );
}
