"use client";

import { useWebSocket } from "@/lib/ws";
import { useEffect, useState } from "react";

type Step = "extract" | "classify" | "summarize" | "embed" | "persist" | "publish";
const STEPS: Step[] = ["extract", "classify", "summarize", "embed", "persist", "publish"];

export function PipelineStatusBar() {
  const ws = useWebSocket();
  const [active, setActive] = useState<Step | null>("summarize");
  const [done, setDone] = useState<Step[]>(["extract", "classify"]);
  const [runId, setRunId] = useState("1847");
  const [tokens, setTokens] = useState(2400);

  useEffect(() => {
    return ws.subscribe((e) => {
      if (e.type === "pipeline.step") {
        const p = e.payload as { run_id: string; step: Step; status: "started"|"done"|"failed"; tokens?: number };
        if (p.status === "started") setActive(p.step);
        if (p.status === "done") {
          setDone((d) => [...new Set([...d, p.step])]);
          setActive(null);
        }
        if (p.tokens) setTokens((t) => t + p.tokens!);
        setRunId(p.run_id);
      }
    });
  }, [ws]);

  return (
    <div className="pointer-events-none fixed bottom-6 left-1/2 z-40 hidden -translate-x-1/2 md:block">
      <div className="pointer-events-auto flex items-center gap-3.5 rounded-xl border border-line-3 px-4 py-3 text-xs glass shadow-2xl"
           style={{ minWidth: 720 }}>
        <span className="text-fg-2 font-medium tracking-[0.04em]">Pipeline</span>
        <div className="flex flex-1 items-center gap-2">
          {STEPS.map((s, i) => {
            const state = done.includes(s) ? "done" : active === s ? "active" : "idle";
            return (
              <div key={s} className="flex items-center gap-2">
                <PipelinePill step={s} state={state} />
                {i < STEPS.length - 1 && <span className="text-fg-3">›</span>}
              </div>
            );
          })}
        </div>
        <span className="mono text-fg-2">run</span>
        <span className="mono">#{runId}</span>
        <span className="h-4 w-px bg-line-2" />
        <span className="mono text-fg-2">tokens</span>
        <span className="mono">{(tokens / 1000).toFixed(1)}k</span>
      </div>
    </div>
  );
}

function PipelinePill({ step, state }: { step: Step; state: "idle"|"active"|"done" }) {
  const cls =
    state === "done"   ? "text-pos border-pos/20"
    : state === "active" ? "text-accent border-accent-line bg-accent-soft"
    : "text-fg-2 border-line-1";
  const dot =
    state === "done"   ? "bg-pos shadow-[0_0_8px_var(--pos)]"
    : state === "active" ? "bg-accent animate-pulse-amber"
    : "bg-fg-3";
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11.5px] font-medium ${cls}`}>
      <span className={`size-1.5 rounded-full ${dot}`} />
      {step}
    </span>
  );
}
