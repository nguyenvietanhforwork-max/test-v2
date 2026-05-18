"use client";

import { useEffect, useState } from "react";
import { useWebSocket } from "@/lib/ws";

interface LiveEvent {
  id: string;
  tag: string;
  cls: "ev-news" | "ev-ok" | "ev-warn";
  body: string;
  time: string;
}

export function RightRail() {
  const [live, setLive] = useState<LiveEvent[]>([]);
  const ws = useWebSocket();

  useEffect(() => {
    const off = ws.subscribe((e) => {
      if (e.type === "pipeline.step" || e.type === "news.created" || e.type === "report.published") {
        const cls: LiveEvent["cls"] = e.type === "pipeline.step" ? "ev-ok" : "ev-news";
        setLive((prev) =>
          [{ id: crypto.randomUUID(), tag: e.type.toUpperCase(), cls,
            body: JSON.stringify(e.payload).slice(0, 80), time: new Date().toTimeString().slice(0,8) }, ...prev].slice(0, 18)
        );
      }
    });
    return () => off();
  }, [ws]);

  return (
    <aside className="hidden flex-col gap-4 overflow-y-auto border-l border-line-1 px-4 pb-20 pt-5 xl:flex">
      <RailCard title="Trending" badge="24h" right="mentions">
        <TrendingList />
      </RailCard>

      <RailCard title="Watchlist" right="VN-Index +0.74%">
        <WatchlistList />
      </RailCard>

      <RailCard title="Live Pipeline" badge="streaming">
        <LiveFeed events={live} />
      </RailCard>
    </aside>
  );
}

function RailCard({ title, badge, right, children }: { title: string; badge?: string; right?: string; children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-xl border border-line-1 bg-bg-1">
      <div className="flex items-center gap-2.5 border-b border-line-1 px-3.5 py-3">
        <h3 className="text-xs font-semibold uppercase tracking-[0.04em] text-fg-1">{title}</h3>
        {badge && <span className="mono rounded border border-accent-line bg-accent-soft px-1.5 py-px text-[10.5px] text-accent">{badge}</span>}
        {right && <span className="mono ml-auto text-[10.5px] text-fg-3">{right}</span>}
      </div>
      {children}
    </div>
  );
}

function TrendingList() {
  const items = [
    { rank: 1, label: "Vingroup", sub: "VIC · Conglomerate", delta: "+42" },
    { rank: 2, label: "Vietcombank", sub: "VCB · Banking", delta: "+31" },
    { rank: 3, label: "Hòa Phát", sub: "HPG · Steel", delta: "+24" },
    { rank: 4, label: "FPT Corp", sub: "FPT · Technology", delta: "+18" },
    { rank: 5, label: "Masan Group", sub: "MSN · Conglomerate", delta: "+14" },
  ];
  return (
    <div className="py-1.5">
      {items.map((t) => (
        <div key={t.rank} className="flex items-center gap-2.5 px-3.5 py-2 hover:bg-bg-2 cursor-pointer">
          <span className="mono w-3.5 text-[10.5px] text-fg-3">{t.rank}</span>
          <div className="flex-1">
            <div className="text-[13px] font-medium">{t.label}</div>
            <div className="text-[11px] text-fg-3">{t.sub}</div>
          </div>
          <span className="mono text-[11.5px] font-semibold text-pos">{t.delta}</span>
        </div>
      ))}
    </div>
  );
}

function WatchlistList() {
  const items = [
    { label: "VCB", sub: "Vietcombank", delta: "+1.84%", pos: true },
    { label: "HPG", sub: "Hòa Phát", delta: "+2.41%", pos: true },
    { label: "FPT", sub: "FPT Corp", delta: "+0.92%", pos: true },
    { label: "VHM", sub: "Vinhomes", delta: "+1.18%", pos: true },
    { label: "MSN", sub: "Masan", delta: "-0.34%", pos: false },
  ];
  return (
    <div className="py-1.5">
      {items.map((w) => (
        <div key={w.label} className="flex items-center gap-2.5 px-3.5 py-2 hover:bg-bg-2 cursor-pointer">
          <span className="mono w-3.5 text-[10.5px] text-accent">★</span>
          <div className="flex-1">
            <div className="text-[13px] font-medium">{w.label}</div>
            <div className="text-[11px] text-fg-3">{w.sub}</div>
          </div>
          <span className={`mono text-[11.5px] font-semibold ${w.pos ? "text-pos" : "text-neg"}`}>{w.delta}</span>
        </div>
      ))}
    </div>
  );
}

function LiveFeed({ events }: { events: LiveEvent[] }) {
  return (
    <div className="px-3.5 pb-3 pt-1.5">
      {events.length === 0 ? (
        <div className="py-3 text-center text-xs text-fg-3">awaiting events…</div>
      ) : (
        events.map((e) => (
          <div key={e.id} className="flex gap-2.5 border-b border-dashed border-line-1 py-2 text-xs last:border-0">
            <span className="mono min-w-[56px] pt-px text-[10.5px] text-fg-3">{e.time}</span>
            <div className="text-fg-1">
              <span className="mono mr-1.5 inline-block rounded border border-line-2 bg-bg-3 px-1.5 py-px text-[9.5px] text-fg-2">{e.tag}</span>
              {e.body}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
