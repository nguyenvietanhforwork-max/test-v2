"use client";

import { useState } from "react";
import { search } from "@/lib/api";

export function SearchPanel() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    try {
      const r = await search(q);
      setHits(r);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <h1 className="font-editorial text-3xl">Semantic Search</h1>
      <form onSubmit={onSearch} className="glass rounded-xl2 p-2 flex">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search across news, wiki, reports…"
          className="flex-1 bg-transparent px-4 py-3 outline-none"
        />
        <button className="chip !text-ink-primary !bg-glass-hover m-1">Search</button>
      </form>
      {loading && <div className="text-ink-dim">Searching…</div>}
      <ul className="space-y-2">
        {hits.map((h) => (
          <li key={h.news_item_id} className="glass rounded-xl p-4">
            <div className="text-sm font-medium">{h.title}</div>
            <div className="text-xs text-ink-dim mt-1">{h.snippet}</div>
            <div className="num text-[10px] mt-2">score {h.score.toFixed(3)}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
