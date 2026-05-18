"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Command } from "cmdk";
import { useEffect, useState, createContext, useContext } from "react";
import { Search, ArrowRight, FileText, GitBranch, LayoutGrid, RefreshCw } from "lucide-react";

const Ctx = createContext<{ open: () => void } | null>(null);

export function useCommandPalette() {
  const ctx = useContext(Ctx);
  return ctx ?? { open: () => {} };
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  return (
    <Ctx.Provider value={{ open: () => setOpen(true) }}>
      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-bg-0/74 backdrop-blur-md data-[state=open]:animate-fade-up" />
          <Dialog.Content className="fixed left-1/2 top-[14vh] z-50 w-[min(680px,92vw)] -translate-x-1/2 overflow-hidden rounded-xl border border-line-3 glass shadow-2xl">
            <Command>
              <div className="flex items-center gap-3 border-b border-line-2 px-4 py-3.5">
                <Search className="size-4 text-fg-2" />
                <Command.Input
                  placeholder="Search news, entities, reports, or run a command…"
                  className="flex-1 bg-transparent text-base outline-none placeholder:text-fg-3"
                />
                <span className="mono text-[11px] text-fg-3">ESC</span>
              </div>
              <Command.List className="max-h-[60vh] overflow-y-auto py-2">
                <Command.Empty className="px-4 py-6 text-center text-sm text-fg-3">No results.</Command.Empty>

                <Command.Group heading="Pages" className="[&_[cmdk-group-heading]]:px-4 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-[10.5px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.14em] [&_[cmdk-group-heading]]:text-fg-3">
                  <Row icon={<LayoutGrid className="size-3.5" />} label="Daily Intelligence" hint="/" />
                  <Row icon={<FileText className="size-3.5" />} label="Report Center" hint="/reports" />
                  <Row icon={<GitBranch className="size-3.5" />} label="Knowledge Graph" hint="/graph" />
                </Command.Group>

                <Command.Group heading="Actions" className="[&_[cmdk-group-heading]]:px-4 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-[10.5px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.14em] [&_[cmdk-group-heading]]:text-fg-3">
                  <Row icon={<RefreshCw className="size-3.5" />} label="Refresh vault" hint="rescan raw/" />
                  <Row icon={<RefreshCw className="size-3.5" />} label="Build daily brief now" hint="run report job" />
                </Command.Group>
              </Command.List>
            </Command>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </Ctx.Provider>
  );
}

function Row({ icon, label, hint }: { icon: React.ReactNode; label: string; hint?: string }) {
  return (
    <Command.Item className="flex items-center gap-3 px-4 py-2.5 text-sm aria-selected:bg-bg-2 aria-selected:text-fg-0">
      <span className="flex size-7 items-center justify-center rounded-md border border-line-2 bg-bg-3 text-fg-1">{icon}</span>
      <span className="flex-1">{label}</span>
      {hint && <span className="mono text-xs text-fg-3">{hint}</span>}
      <ArrowRight className="size-3.5 text-fg-3" />
    </Command.Item>
  );
}
