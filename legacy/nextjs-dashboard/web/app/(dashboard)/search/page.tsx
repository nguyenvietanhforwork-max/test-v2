"use client";

import { useState } from "react";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [mode, setMode] = useState<"lexical" | "semantic" | "hybrid">("hybrid");

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Semantic Search</h1>
      <p className="mt-1 text-sm text-fg-2">Hybrid lexical + vector search across every clipping, report, and wiki page.</p>

      <div className="mt-8 flex items-center gap-3 rounded-xl border border-line-2 bg-bg-1 p-2.5">
        <input
          value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Ask a question, or paste a thesis to find related items…"
          className="flex-1 bg-transparent px-3 py-2 outline-none placeholder:text-fg-3"
        />
        <div className="flex gap-1 rounded-md border border-line-2 bg-bg-2 p-1">
          {(["lexical", "semantic", "hybrid"] as const).map((m) => (
            <button key={m} onClick={() => setMode(m)}
                    className={`mono rounded px-2.5 py-1 text-[11.5px] ${m === mode ? "bg-accent-soft text-accent" : "text-fg-2 hover:text-fg-0"}`}>
              {m}
            </button>
          ))}
        </div>
        <button className="rounded-md bg-accent px-3 py-2 text-sm font-semibold text-bg-0 hover:opacity-90">Search</button>
      </div>

      <div className="mt-10 text-center text-sm text-fg-3">
        {q ? "Wiring up to /api/v1/search …" : "Type a query above to begin."}
      </div>
    </div>
  );
}
