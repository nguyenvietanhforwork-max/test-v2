"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Moon, RefreshCw, Settings, FileText } from "lucide-react";
import { toast } from "sonner";
import { useCommandPalette } from "@/components/search/CommandPalette";
import { vaultRefresh } from "@/lib/api";

export function TopBar() {
  const [clock, setClock] = useState("");
  const [today, setToday] = useState("");
  const [syncing, setSyncing] = useState(false);
  const { open } = useCommandPalette();

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setClock(now.toLocaleTimeString("en-GB", { timeZone: "Asia/Ho_Chi_Minh" }) + " ICT");
      setToday(now.toLocaleDateString("en-GB", { weekday: "short", day: "2-digit", month: "short", year: "numeric", timeZone: "Asia/Ho_Chi_Minh" }));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  async function runSync() {
    setSyncing(true);
    try {
      const result = await vaultRefresh();
      toast.success("Sync queued", { description: `Run ${result.job_id} is processing the vault.` });
    } catch (error) {
      toast.error("Sync failed to start", { description: error instanceof Error ? error.message : "Unknown error" });
    } finally {
      setSyncing(false);
    }
  }

  return (
    <header className="col-span-full flex flex-wrap items-center gap-3 border-b border-line-1 px-4 py-3 xl:flex-nowrap xl:px-5 xl:py-0"
            style={{ background: "linear-gradient(180deg, rgba(12,14,19,0.96), rgba(12,14,19,0.78))", backdropFilter: "blur(24px) saturate(140%)" }}>
      <Brand />
      <div className="flex-1" />
      <Meta clock={clock} today={today} />
      <div className="w-6" />
      <button
        onClick={open}
        className="flex min-w-[220px] items-center gap-3 rounded-lg border border-line-2 bg-bg-2 px-3 py-1.5 text-sm text-fg-2 transition hover:border-line-3 hover:bg-bg-3 md:min-w-[280px]"
      >
        <Search className="size-3.5" />
        <span>Search news, entities, reports…</span>
        <span className="flex-1" />
        <kbd className="mono rounded border border-line-2 bg-bg-2 px-1.5 py-0.5 text-[10.5px]">⌘ K</kbd>
      </button>
      <div className="w-3" />
      <Link
        href="/reports"
        className="inline-flex items-center gap-2 rounded-lg border border-line-2 bg-bg-2 px-3 py-2 text-xs font-medium text-fg-1 transition hover:border-line-3 hover:bg-bg-3"
      >
        <FileText className="size-3.5" />
        Daily Report
      </Link>
      <button
        onClick={runSync}
        disabled={syncing}
        className="inline-flex items-center gap-2 rounded-lg border border-accent-line bg-accent-soft px-3 py-2 text-xs font-semibold text-accent transition hover:bg-bg-3 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <RefreshCw className={`size-3.5 ${syncing ? "animate-spin" : ""}`} />
        {syncing ? "Sync Queued" : "Sync Running"}
      </button>
      <IconBtn title="Theme"><Moon className="size-3.5" /></IconBtn>
      <IconBtn title="Settings"><Settings className="size-3.5" /></IconBtn>
    </header>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5 font-semibold tracking-tight">
      <span className="relative size-6 rounded-md"
            style={{ background: "conic-gradient(from 220deg, var(--accent), var(--violet), var(--cyan), var(--accent))",
                     boxShadow: "0 0 0 1px var(--line-strong) inset, 0 4px 18px rgba(232,184,100,0.18)" }}>
        <span className="absolute inset-[5px] rounded-sm bg-bg-0" />
      </span>
      <span className="text-[15px]">Atlas <span className="text-fg-2 font-medium">/ Intelligence Terminal</span></span>
    </div>
  );
}

function Meta({ clock, today }: { clock: string; today: string }) {
  return (
    <div className="flex items-center gap-4 text-xs text-fg-2">
      <span className="inline-flex items-center gap-2 rounded-full border border-pos/20 bg-pos/10 px-2.5 py-1 text-[11.5px] font-semibold uppercase tracking-[0.06em] text-pos">
        <span className="size-1.5 rounded-full bg-pos animate-pulse" />
        Live
      </span>
      <span className="mono">{clock}</span>
      <span className="text-fg-3">·</span>
      <span className="mono">{today}</span>
      <span className="text-fg-3">·</span>
      <span>VN-Index <span className="mono text-pos">+0.74%</span></span>
      <span className="text-fg-3">·</span>
      <span>USD/VND <span className="mono text-neg">25,418</span></span>
    </div>
  );
}

function IconBtn({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <button title={title} className="flex size-8 items-center justify-center rounded-lg border border-line-2 bg-bg-2 text-fg-1 transition hover:bg-bg-3 hover:border-line-3 ml-2">
      {children}
    </button>
  );
}
