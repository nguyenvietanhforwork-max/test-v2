"use client";

import { useEffect, useRef } from "react";
import { fetchGraph } from "@/lib/api";

/**
 * Lightweight force-directed renderer using d3-force-style math.
 * Production: swap in react-force-graph or sigma.js. This is a stub for layout
 * stability so the page exists in Phase 4 before the heavier integration.
 */
export function GraphView() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    (async () => {
      const data = await fetchGraph(null, 1);
      const canvas = ref.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.fillStyle = "#9aa0a6";
      data.nodes.forEach((n: any, i: number) => {
        const x = 200 + (i * 47) % 800;
        const y = 200 + ((i * 89) % 400);
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillText(n.name, x + 6, y + 4);
      });
    })();
  }, []);

  return (
    <div className="glass rounded-xl2 p-6">
      <h1 className="font-editorial text-3xl mb-4">Knowledge Graph</h1>
      <canvas ref={ref} width={1100} height={600} className="w-full" />
    </div>
  );
}
